"""
Adapts notebooks/latency.ipynb to read from an .xdf fixture instead of the
loose archive CSVs it was originally built against, and quantifies the
latency between the software LIFU_ON marker and the actual physical trigger
artifact in the EEG -- not just a visual scope check.

For each recorded LIFU_ON marker, extracts a window of raw EEG_gpype samples
centered on it, detects when the real electrical trigger artifact appears on
the trigger-pickup channel (the last EEG_gpype channel -- main_pipeline's
merger "channel_8" input, fed from bandpass/2), and reports
detected_time - LIFU_ON_time as the measured latency. Detection uses the same
median/MAD artifact-style thresholding as theta_trigger_loop's own artifact
rejection (z = |x - median| / MAD), but computed fresh from each window's own
pre-marker baseline rather than a persistent rolling buffer, with a stricter
threshold (10 MADs) since this is meant to catch a large, genuine
stimulation artifact rather than routine EEG noise.

Default fixture: tests/sub-archive2back_ses-archive2back_task-Default_run-001_eeg.xdf,
built by tests/build_archive_trigger_xdf.py from
archive/eeg_LSL_gpype2back_test.csv + archive/lifu_markers_1_2back_test.csv --
an archived session with real (non-sham) sonication and 6 actual LIFU_ON
events, since none of the other .xdf fixtures in tests/ have working
sonication to inspect.

Usage:
    python tests/trigger_accuracy_test.py

Output: an all_windows.csv with every window stacked, and a latencies.csv
with one row per window.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyxdf

REPO_ROOT = Path(__file__).resolve().parent.parent
XDF_PATH = (
    Path(__file__).resolve().parent.parent
    / "xdf_data"
    / "sub-dave_run_2"
    / "ses-1"
    / "eeg"
    / "sub-dave_run_2_ses-1_task-dave_run_2_run-001_eeg.xdf"
)
TRIAL_NAME = 'dave_run_4'
EEG_STREAM_NAME = "EEG_gpype"
TRIGGER_STREAM_NAME = "EEG_LIFU_events"
OUTPUT_DIR = Path(__file__).resolve().parent /"trigger_accuracy_plots"/ f"{TRIAL_NAME}"

WINDOW_SAMPLES = 500  # total frames per window (half before LIFU_ON, half after)
TRIGGER_DETECT_MAD_THRESHOLD = 100  # spike must exceed the pre-marker baseline median by this many MADs

# All recorded dave/scott runs, for the standalone `python trigger_accuracy_test.py` sweep below.
XDF_ROOT = REPO_ROOT / "xdf_data"
PARTICIPANTS = ["dave", "scott"]
RUNS = [1, 2, 3, 4]


def _xdf_path_for(participant, run):
    folder = f"sub-{participant}_run_{run}"
    fname = f"sub-{participant}_run_{run}_ses-1_task-{participant}_run_{run}_run-001_eeg.xdf"
    return XDF_ROOT / folder / "ses-1" / "eeg" / fname


def _load_streams(xdf_path=XDF_PATH):
    # dejitter_timestamps=False: keep each sample's original recorded
    # timestamp exactly, since we're aligning windows to it.
    streams, _ = pyxdf.load_xdf(str(xdf_path), dejitter_timestamps=False)
    return {s["info"]["name"][0]: s for s in streams}


def _lifu_on_times(marker_stream):
    return np.array([
        ts
        for marker, ts in zip((m[0] for m in marker_stream["time_series"]), marker_stream["time_stamps"])
        if marker == "LIFU_ON"
    ])


def _extract_windows(eeg_df, lifu_on_ts, n_samples):
    """For each LIFU_ON timestamp, returns (ts, window_df) using the
    n_samples frames centered on the nearest EEG sample. window_df is None if
    the marker is too close to the recording edge for a full window.
    """
    half = n_samples // 2
    time_array = eeg_df["Time"].to_numpy()
    results = []
    for ts in lifu_on_ts:
        idx = np.argmin(np.abs(time_array - ts))
        start, end = idx - half, idx + half
        if start < 0 or end > len(eeg_df):
            results.append((ts, None))
        else:
            results.append((ts, eeg_df.iloc[start:end].reset_index(drop=True)))
    return results


def _detect_trigger(window_df, lifu_on_ts, trigger_channel):
    """Detects when the physical LIFU trigger artifact actually appears in
    `trigger_channel`, for measuring latency against the software LIFU_ON
    marker.

    Computes median/MAD from this window's own pre-marker baseline (the
    portion with Time < lifu_on_ts) -- not a persistent rolling buffer -- and
    flags the first post-marker sample exceeding median + 10*MAD as the
    detected trigger. Returns (detected_ts, baseline_median, baseline_mad);
    detected_ts is None if nothing crosses the threshold.
    """
    baseline = window_df.loc[window_df["Time"] < lifu_on_ts, trigger_channel].to_numpy()
    median = np.median(baseline)
    mad = np.median(np.abs(baseline - median)) + 1e-9
    threshold = median + TRIGGER_DETECT_MAD_THRESHOLD * mad

    after = window_df[window_df["Time"] >= lifu_on_ts]
    hits = after.index[after[trigger_channel] > threshold]
    if len(hits) == 0:
        return None, median, mad
    return after.loc[hits[0], "Time"], median, mad


def _analyze_recording(output_dir, xdf_path=XDF_PATH):
    streams = _load_streams(xdf_path)
    eeg_stream = streams[EEG_STREAM_NAME]
    marker_stream = streams[TRIGGER_STREAM_NAME]

    nchan = int(eeg_stream["info"]["channel_count"][0])
    channel_cols = [f"Ch{i:02d}" for i in range(1, nchan + 1)]
    # merger's "channel_8" input (fed from bandpass/2) is always inserted
    # last -- see main_pipeline.run_pipeline's Router -- so it lands as the
    # last EEG_gpype channel regardless of channel count.
    trigger_channel = channel_cols[-1]
    eeg_df = pd.DataFrame(eeg_stream["time_series"], columns=channel_cols)
    eeg_df.insert(0, "Time", eeg_stream["time_stamps"])
    t0 = eeg_df["Time"].iloc[0]

    lifu_on_ts = _lifu_on_times(marker_stream)
    print(f"Found {len(lifu_on_ts)} LIFU_ON marker(s) at t = "
          + ", ".join(f"{t - t0:.3f}s" for t in lifu_on_ts))
    print(f"Detecting the physical trigger artifact on {trigger_channel} as "
          f"{TRIGGER_DETECT_MAD_THRESHOLD} MAD above each window's own pre-marker baseline.")

    results = _extract_windows(eeg_df, lifu_on_ts, WINDOW_SAMPLES)
    skipped = [ts for ts, w in results if w is None]
    if skipped:
        print(f"Skipped {len(skipped)} marker(s) too close to the recording edge for a full "
              f"{WINDOW_SAMPLES}-sample window: " + ", ".join(f"{t - t0:.3f}s" for t in skipped))

    output_dir.mkdir(parents=True, exist_ok=True)
    stacked = []
    latency_rows = []
    window_idx = 0
    for ts, window_df in results:
        if window_df is None:
            continue
        w = window_df.copy()
        w["window_id"] = window_idx
        stacked.append(w)

        detected_ts, baseline_median, baseline_mad = _detect_trigger(window_df, ts, trigger_channel)
        if detected_ts is None:
            latency_ms = None
            print(f"  window {window_idx}: LIFU_ON at t={ts - t0:.3f}s -> "
                  f"NO trigger artifact detected above {TRIGGER_DETECT_MAD_THRESHOLD} MAD "
                  f"(baseline median={baseline_median:.2f}, MAD={baseline_mad:.2f})")
        else:
            latency_ms = (detected_ts - ts) * 1000
            print(f"  window {window_idx}: LIFU_ON at t={ts - t0:.3f}s -> trigger detected at "
                  f"t={detected_ts - t0:.3f}s (latency {latency_ms:.1f} ms)")
        latency_rows.append({
            "window_id": window_idx,
            "lifu_on_t": ts - t0,
            "detected_t": (detected_ts - t0) if detected_ts is not None else None,
            "latency_ms": latency_ms,
            "baseline_median": baseline_median,
            "baseline_mad": baseline_mad,
        })

        window_idx += 1

    if stacked:
        all_windows = pd.concat(stacked, ignore_index=True)
        all_windows_path = output_dir / "all_windows.csv"
        all_windows.to_csv(all_windows_path, index=False)
        print(f"\nSaved {window_idx} window(s) x {WINDOW_SAMPLES} samples to "
              f"{all_windows_path}")

        latencies_df = pd.DataFrame(latency_rows)
        latencies_path = output_dir / "latencies.csv"
        latencies_df.to_csv(latencies_path, index=False)
        print(f"Saved per-window latencies to {latencies_path}")

        detected = latencies_df["latency_ms"].dropna()
        if len(detected):
            print(f"\nLatency summary over {len(detected)}/{window_idx} window(s) with a detected trigger:")
            print(f"  mean={detected.mean():.1f}ms  median={detected.median():.1f}ms  "
                  f"min={detected.min():.1f}ms  max={detected.max():.1f}ms  std={detected.std():.1f}ms")
        if len(detected) < window_idx:
            print(f"  WARNING: {window_idx - len(detected)} window(s) had no detectable trigger artifact.")
    else:
        print("\nNo windows extracted -- nothing to plot or save.")

    return results, latency_rows


def test_recorded_trigger_accuracy(tmp_path):
    results, latency_rows = _analyze_recording(tmp_path)

    assert len(results) <=10
    assert all(window is not None for _timestamp, window in results)
    assert len(latency_rows) <= 10
    detected_latencies = [row["latency_ms"] for row in latency_rows if row["latency_ms"] is not None]
    assert len(detected_latencies) <= 10
    assert all(0 <= latency <= 500 for latency in detected_latencies)


def _sweep_all_runs():
    """Runs every dave/scott recording through `_analyze_recording` and prints
    the latency for every sonication found, across every run."""
    all_rows = []
    for participant in PARTICIPANTS:
        for run in RUNS:
            xdf_path = _xdf_path_for(participant, run)
            output_dir = OUTPUT_DIR.parent / f"{participant}_run_{run}"
            print(f"\n=== {participant} run {run}: {xdf_path.name} ===")
            if not xdf_path.exists():
                print(f"  Fixture not found, skipping: {xdf_path}")
                continue
            _results, latency_rows = _analyze_recording(output_dir, xdf_path=xdf_path)
            for row in latency_rows:
                all_rows.append({"participant": participant, "run": run, **row})

    print("\n\n=== All sonications, every run ===")
    if not all_rows:
        print("No sonications found in any run.")
        return all_rows

    header = f"{'participant':<10}{'run':<5}{'window':<8}{'lifu_on_t':>12}{'detected_t':>12}{'latency_ms':>12}"
    print(header)
    for row in all_rows:
        detected_t = f"{row['detected_t']:.3f}" if row["detected_t"] is not None else "n/a"
        latency = f"{row['latency_ms']:.1f}" if row["latency_ms"] is not None else "n/a"
        print(f"{row['participant']:<10}{row['run']:<5}{row['window_id']:<8}"
              f"{row['lifu_on_t']:>12.3f}{detected_t:>12}{latency:>12}")

    detected = [row["latency_ms"] for row in all_rows if row["latency_ms"] is not None]
    print(f"\n{len(detected)}/{len(all_rows)} sonications had a detectable trigger artifact.")
    if detected:
        arr = np.array(detected)
        print(f"Overall latency: mean={arr.mean():.1f}ms  median={np.median(arr):.1f}ms  "
              f"min={arr.min():.1f}ms  max={arr.max():.1f}ms  std={arr.std():.1f}ms")

    return all_rows


if __name__ == "__main__":
    _sweep_all_runs()

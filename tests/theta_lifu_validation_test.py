"""
Runs main_pipeline.theta_trigger_loop directly over a recorded EEG_gpype
stream (no LSL involved) and compares the LIFU_ON times it produces
("offline") against the LIFU_ON times actually recorded live in the same
xdf's EEG_LIFU_events stream ("online").

theta_trigger_loop takes an optional `sample_source` iterable of (theta_val,
ts) pairs (see main_pipeline.theta_sample_source for the live-LSL default).
Feeding it recorded (theta_val, ts) pairs directly -- using each sample's own
recorded timestamp -- exercises the exact same decision logic and
push_sample() marker emission as production, deterministically.

Usage:
    python tests/theta_lifu_validation_test.py
"""
from __future__ import annotations

import contextlib
import io
import sys
import types
from pathlib import Path

import numpy as np
import pyxdf

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# main_pipeline imports the openlifu hardware stack purely to construct
# objects theta_trigger_loop never touches (those calls are commented out in
# the source). If openlifu isn't importable in this environment (e.g. an
# onnxruntime/numpy ABI mismatch), stub the modules it imports so we can still
# exercise the real theta_trigger_loop function without needing working
# hardware bindings.
def _stub_module(name, **attrs):
    mod = types.ModuleType(name)
    for attr, value in attrs.items():
        setattr(mod, attr, value)
    sys.modules[name] = mod
    return mod


try:
    import openlifu  # noqa: F401
except ImportError:
    _stub_module("openlifu")
    _stub_module("openlifu.bf")
    _stub_module("openlifu.bf.pulse", Pulse=object)
    _stub_module("openlifu.bf.sequence", Sequence=object)
    _stub_module("openlifu.db", Database=object)
    _stub_module("openlifu.geo", Point=object)
    _stub_module("openlifu.io")
    _stub_module("openlifu.io.LIFUInterface", LIFUInterface=object)
    _stub_module("openlifu.plan")
    _stub_module("openlifu.plan.solution", Solution=object)

import main_pipeline  # noqa: E402


XDF_PATH = Path(__file__).resolve().parent.parent / "xdf_data\\sub-test\\ses-1\\eeg\\sub-test_ses-1_task-test_run-001_eeg.xdf"
EEG_STREAM_NAME = "EEG_gpype"
TRIGGER_STREAM_NAME = "EEG_LIFU_events"
THETA_CHANNEL_INDEX = 11


class _RecordingOutlet:
    """Stand-in for main_pipeline.eeg_trigger_outlet. theta_trigger_loop calls
    .push_sample([marker]) verbatim; this records (marker, ts) using the
    timestamp of whichever recorded sample is currently being fed, instead of
    transmitting anything over LSL.
    """

    def __init__(self, events, current_ts_holder):
        self._events = events
        self._current_ts_holder = current_ts_holder

    def push_sample(self, sample, *args, **kwargs):
        self._events.append((sample[0], self._current_ts_holder["ts"]))


class _NoOpOutlet:
    """Stand-in for main_pipeline.lifu_num_outlet -- its numeric 1.0/0.0
    samples aren't needed for this comparison, just swallow them."""

    def push_sample(self, sample, *args, **kwargs):
        pass


def _load_streams():
    streams, _ = pyxdf.load_xdf(str(XDF_PATH), dejitter_timestamps=False)
    return {s["info"]["name"][0]: s for s in streams}


def _find_marker_time(marker_stream, marker_name):
    for sample, ts in zip(marker_stream["time_series"], marker_stream["time_stamps"]):
        if sample[0] == marker_name:
            return ts
    return None


def _recorded_sample_source(eeg_stream, current_ts_holder, sonication_start_ts):
    """Yields (theta_val, ts) pairs from the recorded EEG_gpype channel, in
    order, tagged with each sample's own recorded timestamp. Flips
    main_pipeline.experiment_started True once the replay reaches the
    recorded moment sonication was actually enabled live -- mirroring
    listen_for_start() without using LSL to do it.
    """
    for sample, ts in zip(eeg_stream["time_series"], eeg_stream["time_stamps"]):
        if sonication_start_ts is not None and ts >= sonication_start_ts:
            main_pipeline.experiment_started = True
        current_ts_holder["ts"] = ts
        yield sample[THETA_CHANNEL_INDEX], ts


def _run_with_sample_source(sample_source, current_ts_holder):
    """Runs the real main_pipeline.theta_trigger_loop against `sample_source`
    (an iterable of (theta_val, ts) pairs that is itself responsible for
    updating current_ts_holder["ts"] and flipping
    main_pipeline.experiment_started at the right point), capturing every
    push_sample(...) call without any LSL involved. Returns the raw
    (marker, ts) event list.
    """
    main_pipeline.RUNNING = True

    events = []
    real_eeg_trigger_outlet = main_pipeline.eeg_trigger_outlet
    real_lifu_num_outlet = main_pipeline.lifu_num_outlet
    main_pipeline.eeg_trigger_outlet = _RecordingOutlet(events, current_ts_holder)
    main_pipeline.lifu_num_outlet = _NoOpOutlet()

    try:
        # theta_trigger_loop prints a line on every accepted sample; swallow
        # it so tens of thousands of lines don't drown out the results below.
        with contextlib.redirect_stdout(io.StringIO()):
            main_pipeline.theta_trigger_loop(sample_source=sample_source)
    finally:
        main_pipeline.eeg_trigger_outlet = real_eeg_trigger_outlet
        main_pipeline.lifu_num_outlet = real_lifu_num_outlet

    return events


def _stream_gap_report(eeg_stream, center_ts, window_s=1.0, ratio_threshold=1.5):
    """Checks eeg_stream's own recorded timestamps within +/- window_s of
    center_ts (absolute LSL time) for irregular sample-to-sample intervals,
    relative to the stream's overall median interval.

    Used to tell whether an online/offline LIFU_ON mismatch coincides with a
    real hiccup in the recorded EEG_gpype stream (e.g. a dropped or
    duplicated sample from whichever LSL consumer produced this recording)
    rather than a decision-logic bug -- the two consumers (this recording and
    theta_trigger_loop's own live inlet) are independent, so a stall on
    either side can make them settle on different samples without the
    decision logic itself disagreeing.
    """
    ts_arr = np.asarray(eeg_stream["time_stamps"])
    all_diffs = np.diff(ts_arr)
    nominal = float(np.median(all_diffs))

    mask = (ts_arr[:-1] >= center_ts - window_s) & (ts_arr[:-1] <= center_ts + window_s)
    anomalies = []
    for i in np.nonzero(mask)[0]:
        gap = float(all_diffs[i])
        ratio = gap / nominal if nominal else float("inf")
        if ratio > ratio_threshold or ratio < 1 / ratio_threshold:
            anomalies.append((float(ts_arr[i]), gap, ratio))
    return nominal, anomalies


def run():
    streams = _load_streams()
    eeg_stream = streams[EEG_STREAM_NAME]
    lifu_stream = streams[TRIGGER_STREAM_NAME]
    t0 = eeg_stream["time_stamps"][0]

    sonication_start_ts = _find_marker_time(lifu_stream, "START_EXPERIMENT_RECEIVED")
    if sonication_start_ts is None:
        print("WARNING: no START_EXPERIMENT_RECEIVED marker found; enabling sonication from the first sample.")
        sonication_start_ts = t0

    main_pipeline.experiment_started = False
    current_ts_holder = {"ts": None}
    sample_source = _recorded_sample_source(eeg_stream, current_ts_holder, sonication_start_ts)
    events = _run_with_sample_source(sample_source, current_ts_holder)

    offline_on = sorted(ts - t0 for marker, ts in events if marker == "LIFU_ON")
    online_on = sorted(
        ts - t0
        for marker, ts in zip((m[0] for m in lifu_stream["time_series"]), lifu_stream["time_stamps"])
        if marker == "LIFU_ON"
    )

    print("offline (re-run)   LIFU_ON: " + ", ".join(f"{t:.3f}s" for t in offline_on))
    print("online  (recorded) LIFU_ON: " + ", ".join(f"{t:.3f}s" for t in online_on))

    n = min(len(offline_on), len(online_on))
    if n:
        diffs = [online_on[i] - offline_on[i] for i in range(n)]
        print(f"\ndiff (online - offline) for first {n} matched event(s), seconds:")
        print(", ".join(f"{d:+.3f}" for d in diffs))

        GAP_CHECK_THRESHOLD_S = 0.010  # diffs bigger than this get a stream-gap diagnostic
        for i, d in enumerate(diffs):
            if abs(d) <= GAP_CHECK_THRESHOLD_S:
                continue
            center_ts = t0 + online_on[i]
            nominal, anomalies = _stream_gap_report(eeg_stream, center_ts)
            print(f"\n  event {i}: diff={d:+.3f}s exceeds {GAP_CHECK_THRESHOLD_S}s threshold -- "
                  f"checking EEG_gpype timestamps near t={online_on[i]:.3f}s "
                  f"(stream's nominal sample interval {nominal * 1000:.2f}ms):")
            if anomalies:
                for ts_at, gap, ratio in anomalies:
                    print(f"    anomaly at t={ts_at - t0:.3f}s: interval={gap * 1000:.2f}ms "
                          f"({ratio:.1f}x nominal) -- likely dropped/duplicated sample here")
            else:
                print("    no timestamp irregularities found near this event -- "
                      "mismatch isn't explained by a recording gap.")
    if len(offline_on) != len(online_on):
        print(f"\nWARNING: {len(offline_on)} offline vs {len(online_on)} online LIFU_ON -- count mismatch.")

    return offline_on, online_on


# ---------------------------------------------------------------------------
# Synthetic test cases: rather than replaying a recording, these construct a
# theta_val sequence by hand so the correct behavior is known analytically
# up front, and assert against it directly (PASS/FAIL) instead of just
# diffing against a reference.
FS = 250.0
DT = 1.0 / FS
TOLERANCE_S = 0.01  # 10ms: comfortably above float/grid rounding, tight vs. a 15s cooldown


def _sine_values(n, center, amplitude, freq_hz):
    """A smooth sine wave sampled at FS, rather than an instant square-wave
    alternation. theta_trigger_loop's rolling artifact-rejection buffer is a
    running median/MAD -- feeding it a perfectly bimodal square wave (flip
    between exactly two fixed values every sample) can make the buffer's
    accept/reject rates skew asymmetrically and collapse onto a single value
    over time, which is a real quirk of that design but not representative of
    continuous EEG data. A continuously-varying signal avoids it, and also
    naturally avoids exact-repeat dedup without needing extra jitter.
    """
    import math
    return [center + amplitude * math.sin(2 * math.pi * freq_hz * (i * DT)) for i in range(n)]


def _synthetic_sample_source(theta_values, current_ts_holder, sonication_start_ts):
    """Yields (theta_val, ts) pairs from a synthetic theta_values sequence
    sampled at FS starting at t=0, flipping main_pipeline.experiment_started
    True once ts reaches sonication_start_ts -- mirroring the real
    START_EXPERIMENT_RECEIVED gate (listen_for_start()) without any LSL.
    """
    for i, theta_val in enumerate(theta_values):
        ts = i * DT
        if sonication_start_ts is not None and ts >= sonication_start_ts:
            main_pipeline.experiment_started = True
        current_ts_holder["ts"] = ts
        yield theta_val, ts


def test_constant_above_threshold():
    """EEG data sits constantly inside the trigger band (THETA_THRESHOLD_Z,
    MAD_THRESHOLD) for the whole recording. Since the threshold condition is
    never the limiting factor, theta_trigger_loop should sonicate as soon as
    each COOLDOWN_TIME window permits -- i.e. exactly every 15 seconds, no
    more and no less often.
    """
    print("\n=== test_constant_above_threshold ===")
    center, amplitude = 3.0, 0.3  # stays in [2.7, 3.3] -- comfortably inside (THETA_THRESHOLD_Z=1.5, MAD_THRESHOLD=6)
    duration_s = 50.0
    sonication_start_ts = 5.0  # START_EXPERIMENT_RECEIVED equivalent, well before any possible trigger

    theta_values = _sine_values(int(duration_s / DT), center, amplitude, freq_hz=1.0)
    main_pipeline.experiment_started = False
    current_ts_holder = {"ts": None}
    sample_source = _synthetic_sample_source(theta_values, current_ts_holder, sonication_start_ts)
    events = _run_with_sample_source(sample_source, current_ts_holder)

    on_times = sorted(ts for marker, ts in events if marker == "LIFU_ON")
    print("LIFU_ON at t = " + ", ".join(f"{t:.3f}s" for t in on_times))

    checks = []
    checks.append(("at least 2 triggers to compare spacing", len(on_times) >= 2))
    checks.append((
        f"no trigger before sonication_start_ts ({sonication_start_ts}s)",
        all(t >= sonication_start_ts for t in on_times),
    ))
    if on_times:
        checks.append((
            f"first trigger fires at the earliest legal instant (~{main_pipeline.COOLDOWN_TIME}s, "
            "since last_trigger_time starts at 0)",
            main_pipeline.COOLDOWN_TIME < on_times[0] <= main_pipeline.COOLDOWN_TIME + TOLERANCE_S,
        ))
    for a, b in zip(on_times, on_times[1:]):
        spacing = b - a
        checks.append((
            f"spacing {a:.3f}s -> {b:.3f}s is exactly COOLDOWN_TIME ({spacing:.3f}s ~ "
            f"{main_pipeline.COOLDOWN_TIME}s)",
            main_pipeline.COOLDOWN_TIME <= spacing <= main_pipeline.COOLDOWN_TIME + TOLERANCE_S,
        ))

    return _report(checks)


def test_oscillating_threshold():
    """EEG data oscillates between clearly below threshold and clearly
    within the trigger band. theta_trigger_loop should only ever sonicate
    while the value is actually in-band, should never violate the cooldown
    even though the value swings back into band multiple times per cooldown
    window, and should never fire before experiment_started is set (the
    START_EXPERIMENT_RECEIVED gate).
    """
    print("\n=== test_oscillating_threshold ===")
    period_s = 12.0  # theta_val = 1.5 + 1.5*sin(2*pi*t/period_s) -> oscillates over [0.0, 3.0],
    #                  crossing THETA_THRESHOLD_Z=1.5 twice per period (once rising, once falling)
    duration_s = 80.0
    sonication_start_ts = 20.0  # START_EXPERIMENT_RECEIVED equivalent -- deliberately mid-oscillation

    theta_values = _sine_values(int(duration_s / DT), center=1.5, amplitude=1.5, freq_hz=1.0 / period_s)

    def _is_high(ts):
        # matches the sign of the sine used to build theta_values above
        import math
        return math.sin(2 * math.pi * (1.0 / period_s) * ts) > 0

    main_pipeline.experiment_started = False
    current_ts_holder = {"ts": None}
    sample_source = _synthetic_sample_source(theta_values, current_ts_holder, sonication_start_ts)
    events = _run_with_sample_source(sample_source, current_ts_holder)

    on_times = sorted(ts for marker, ts in events if marker == "LIFU_ON")
    print("LIFU_ON at t = " + ", ".join(f"{t:.3f}s" for t in on_times))

    checks = []
    checks.append(("at least 2 triggers occurred", len(on_times) >= 2))
    checks.append((
        f"no trigger before sonication_start_ts ({sonication_start_ts}s)",
        all(t >= sonication_start_ts for t in on_times),
    ))
    checks.append((
        "every trigger landed while theta_val was actually above THETA_THRESHOLD_Z, never during a low swing",
        all(_is_high(t) for t in on_times),
    ))
    for a, b in zip(on_times, on_times[1:]):
        checks.append((
            f"cooldown respected between {a:.3f}s and {b:.3f}s (spacing {b - a:.3f}s >= "
            f"COOLDOWN_TIME {main_pipeline.COOLDOWN_TIME}s)",
            (b - a) >= main_pipeline.COOLDOWN_TIME - 1e-9,
        ))

    return _report(checks)


def _report(checks):
    all_ok = True
    for description, passed in checks:
        print(f"  {'PASS' if passed else 'FAIL'}  {description}")
        all_ok = all_ok and passed
    print("RESULT:", "PASS" if all_ok else "FAIL")
    return all_ok


if __name__ == "__main__":
    run()

    results = {
        "test_constant_above_threshold": test_constant_above_threshold(),
        "test_oscillating_threshold": test_oscillating_threshold(),
    }

    print("\n=== Summary ===")
    for name, passed in results.items():
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")

    print("\nTest complete.")
    if not all(results.values()):
        sys.exit(1)

"""
Validates main_pipeline.theta_trigger_loop -- the actual production function,
decision logic and LIFU marker emission included -- against a recorded
session, with no LSL involved at all.

theta_trigger_loop takes an optional `sample_source` iterable of (theta_val,
ts) pairs (see main_pipeline.theta_sample_source for the live-LSL default).
This test builds that iterable directly from the recorded EEG_gpype channel
in the xdf file, using each sample's own recorded timestamp -- exactly the
`ts` theta_trigger_loop would have seen live. Because feeding is synchronous
(no threads, no network), the timestamp of the sample being fed at the moment
a marker is pushed is known exactly, with no wall-clock jitter or pacing
required.

To capture that without a real LSL stream, main_pipeline.eeg_trigger_outlet /
lifu_num_outlet (the two globals theta_trigger_loop calls .push_sample() on)
are swapped for a recorder object for the duration of the run. This does not
touch theta_trigger_loop's logic -- it calls the exact same .push_sample(...)
it always does, just against a stand-in that records (marker, ts) instead of
transmitting over LSL.

Usage:
    python tests/theta_lifu_validation_test.py

Then fill in EXPECTED_LIFU_ON_SECONDS below with the times you manually
expect LIFU_ON to fire (seconds since the first EEG_gpype sample) and re-run
-- the script will report PASS/FAIL per expected time.
"""
from __future__ import annotations

import contextlib
import io
import sys
import time
import types
from pathlib import Path

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

# main_pipeline also imports hash_func, which just derives a string used to
# name its output CSV files (unrelated to theta_trigger_loop) but requires
# the murmurhash package. Stub it too if it's not installed, rather than
# pulling in a dependency this test doesn't need.
try:
    import hash_func  # noqa: F401
except ImportError:
    _stub_module("hash_func", hash_and_test="theta_lifu_validation_test")

import main_pipeline  # noqa: E402


XDF_PATH = Path(__file__).resolve().parent / "sub-demo_ses-demo_task-Default_run-001_eeg.xdf"
EEG_STREAM_NAME = "EEG_gpype"
TRIGGER_STREAM_NAME = "EEG_LIFU_events"
THETA_CHANNEL_INDEX = 11

# ---------------------------------------------------------------------------
# Fill this in with the second-marks (relative to the first EEG_gpype sample)
# where you expect LIFU_ON to fire, e.g. [12.9, 29.8, 49.7], then re-run.
EXPECTED_LIFU_ON_SECONDS: list[float] = []
TOLERANCE_SECONDS = 0.1


class _RecordingOutlet:
    """Stand-in for main_pipeline's real LSL StreamOutlet objects.

    theta_trigger_loop calls outlet.push_sample([marker]) verbatim -- this
    object accepts that same call and records (marker, ts) using the
    timestamp of whichever recorded sample is currently being fed, instead of
    transmitting anything over LSL.
    """

    def __init__(self, name, events, current_ts_holder):
        self.name = name
        self._events = events
        self._current_ts_holder = current_ts_holder

    def push_sample(self, sample, *args, **kwargs):
        self._events.append((self.name, sample[0], self._current_ts_holder["ts"]))


def _load_streams():
    streams, _ = pyxdf.load_xdf(str(XDF_PATH))
    return {s["info"]["name"][0]: s for s in streams}


def _find_marker_time(marker_stream, marker_name):
    for sample, ts in zip(marker_stream["time_series"], marker_stream["time_stamps"]):
        if sample[0] == marker_name:
            return ts
    return None


def _recorded_sample_source(eeg_stream, current_ts_holder, sonication_start_ts):
    """Yields (theta_val, ts) pairs straight from the recorded EEG_gpype
    channel, in original order, tagged with each sample's own recorded
    timestamp. Flips main_pipeline.sonication_enabled True once the replay
    reaches the recorded moment sonication was actually enabled live --
    exactly mirroring what listen_for_start() would have done, without using
    LSL to do it.
    """
    for sample, ts in zip(eeg_stream["time_series"], eeg_stream["time_stamps"]):
        if sonication_start_ts is not None and ts >= sonication_start_ts:
            main_pipeline.sonication_enabled = True
        current_ts_holder["ts"] = ts
        yield sample[THETA_CHANNEL_INDEX], ts


def _check_against_expected(on_times):
    expected = sorted(EXPECTED_LIFU_ON_SECONDS)
    print(f"\nComparing against {len(expected)} expected LIFU_ON time(s) "
          f"(tolerance = {TOLERANCE_SECONDS}s):")
    unmatched_actual = list(on_times)
    all_ok = True
    for exp in expected:
        best = min(unmatched_actual, key=lambda t: abs(t - exp), default=None)
        if best is not None and abs(best - exp) <= TOLERANCE_SECONDS:
            print(f"  PASS  expected {exp:7.3f}s -> matched {best:7.3f}s "
                  f"(diff {abs(best - exp) * 1000:.0f}ms)")
            unmatched_actual.remove(best)
        else:
            print(f"  FAIL  expected {exp:7.3f}s -> no produced trigger within tolerance")
            all_ok = False
    for extra in unmatched_actual:
        print(f"  FAIL  unexpected LIFU_ON produced at {extra:7.3f}s with no matching expected time")
        all_ok = False
    print("\nRESULT:", "ALL PASS" if all_ok else "SOME FAILURES")


def run():
    streams = _load_streams()
    eeg_stream = streams[EEG_STREAM_NAME]
    t0_recorded = eeg_stream["time_stamps"][0]
    duration = eeg_stream["time_stamps"][-1] - t0_recorded

    sonication_start_ts = None
    if TRIGGER_STREAM_NAME in streams:
        sonication_start_ts = _find_marker_time(streams[TRIGGER_STREAM_NAME], "START_EXPERIMENT_RECEIVED")
    if sonication_start_ts is None:
        print(f"WARNING: no START_EXPERIMENT_RECEIVED marker found in {TRIGGER_STREAM_NAME}; "
              "enabling sonication from the first sample instead.")
        sonication_start_ts = t0_recorded

    main_pipeline.sonication_enabled = False
    main_pipeline.NUM_SONICATIONS = 0
    main_pipeline.RUNNING = True

    events = []
    current_ts_holder = {"ts": None}
    real_eeg_trigger_outlet = main_pipeline.eeg_trigger_outlet
    real_lifu_num_outlet = main_pipeline.lifu_num_outlet
    main_pipeline.eeg_trigger_outlet = _RecordingOutlet("eeg_trigger", events, current_ts_holder)
    main_pipeline.lifu_num_outlet = _RecordingOutlet("lifu_num", events, current_ts_holder)

    print(f"Feeding {len(eeg_stream['time_stamps'])} recorded EEG_gpype samples "
          f"({duration:.1f}s of recording) directly into theta_trigger_loop, no LSL involved.")
    print(f"sonication_enabled will flip True at recorded t = {sonication_start_ts - t0_recorded:.3f}s.")
    print("(suppressing theta_trigger_loop's own per-sample print() output)")

    wall_start = time.perf_counter()
    sample_source = _recorded_sample_source(eeg_stream, current_ts_holder, sonication_start_ts)
    try:
        # theta_trigger_loop prints a line on every accepted sample; swallow
        # it so tens of thousands of lines don't drown out the results below.
        # The real time.sleep(SONICATION_TIME) inside theta_trigger_loop
        # still runs for real on every genuine trigger.
        with contextlib.redirect_stdout(io.StringIO()):
            main_pipeline.theta_trigger_loop(sample_source=sample_source)
    finally:
        main_pipeline.eeg_trigger_outlet = real_eeg_trigger_outlet
        main_pipeline.lifu_num_outlet = real_lifu_num_outlet
    wall_elapsed = time.perf_counter() - wall_start

    on_times = sorted(ts - t0_recorded for outlet, marker, ts in events if marker == "LIFU_ON")
    off_count = sum(1 for outlet, marker, ts in events if marker == "LIFU_OFF")
    # LIFU_OFF fires after a real time.sleep(SONICATION_TIME) inside
    # theta_trigger_loop, during which no further recorded samples are fed
    # (the generator is paused), so there's no recorded sample to correlate
    # it with. Its true recorded-time is definitionally ON + SONICATION_TIME,
    # which is what we report rather than the (stale) correlated timestamp.
    off_times = sorted(t + main_pipeline.SONICATION_TIME for t in on_times)

    print(f"\nDone in {wall_elapsed:.1f}s real time.")
    print(f"\n{len(on_times)} LIFU_ON produced at t = " + ", ".join(f"{t:.3f}s" for t in on_times))
    print(f"{off_count} LIFU_OFF produced ({main_pipeline.SONICATION_TIME}s after each ON) at t = "
          + ", ".join(f"{t:.3f}s" for t in off_times))
    if off_count != len(on_times):
        print(f"WARNING: {len(on_times)} LIFU_ON but {off_count} LIFU_OFF -- mismatched count!")

    # Reference-only: the LIFU_ON times actually recorded live in this xdf
    # file, for a quick sanity comparison while you assemble your own
    # expected times.
    if TRIGGER_STREAM_NAME in streams:
        recorded_on = sorted(
            ts - t0_recorded
            for marker, ts in zip(
                (m[0] for m in streams[TRIGGER_STREAM_NAME]["time_series"]),
                streams[TRIGGER_STREAM_NAME]["time_stamps"],
            )
            if marker == "LIFU_ON"
        )
        print(f"\n(reference) {len(recorded_on)} LIFU_ON recorded live in this xdf at t = "
              + ", ".join(f"{t:.3f}s" for t in recorded_on))

    if EXPECTED_LIFU_ON_SECONDS:
        _check_against_expected(on_times)
    else:
        print("\nNo EXPECTED_LIFU_ON_SECONDS set yet -- fill in that list at the top of this "
              "file with your manually-determined times and re-run for a PASS/FAIL check.")


if __name__ == "__main__":
    run()
    print("\nTest complete.")

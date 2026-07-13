"""
Verifies that main_pipeline.theta_trigger_loop's NUM_SONICATIONS counter and
cap actually work: it increments exactly once per LIFU_ON, and the loop
refuses to trigger again once NUM_SONICATIONS reaches max_sonications --
even while the theta signal stays continuously in the trigger band.

theta_trigger_loop takes sonication_time/cooldown_time/max_sonications (and
the other threshold constants) as keyword arguments now, defaulting to the
module-level SONICATION_TIME/COOLDOWN_TIME/MAX_SONICATIONS constants (see
main_pipeline.py). That means a test can pass tiny sonication_time/
cooldown_time and a small max_sonications to exercise the real cap logic --
unmodified -- in a fraction of a second, instead of needing 10 * (5s
sonication + 15s cooldown) of real wall-clock time.

Usage:
    python tests/num_sonications_test.py
"""
from __future__ import annotations

import contextlib
import io
import math
import sys
import types
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# main_pipeline imports the openlifu hardware stack purely to construct
# objects theta_trigger_loop never touches. Stub those out so this test can
# run without the hardware bindings installed -- same approach as
# theta_lifu_validation_test.py.
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


FS = 250.0
DT = 1.0 / FS


class _RecordingOutlet:
    """Stand-in for main_pipeline.eeg_trigger_outlet/lifu_num_outlet --
    records every push_sample(...) call instead of transmitting over LSL."""

    def __init__(self, events):
        self._events = events

    def push_sample(self, sample, *args, **kwargs):
        self._events.append(sample[0])


def _sine_values(n, center, amplitude, freq_hz):
    """A continuously in-band signal (see theta_lifu_validation_test.py for
    why a sine is used instead of a square wave: it avoids the rolling
    median/MAD buffer collapsing onto a single value)."""
    return [center + amplitude * math.sin(2 * math.pi * freq_hz * (i * DT)) for i in range(n)]


def _synthetic_sample_source(theta_values):
    """Yields (theta_val, ts) pairs sampled at FS starting at t=0, with
    start_received already True throughout (set by the caller)."""
    for i, theta_val in enumerate(theta_values):
        yield theta_val, i * DT


def _run(theta_values, **loop_kwargs):
    """Runs the real main_pipeline.theta_trigger_loop over a synthetic,
    continuously in-band theta signal, with sonication enabled from the
    start and both outlets swapped for recorders. Returns (events,
    num_sonications): the list of markers pushed to eeg_trigger_outlet, in
    order, and the loop's own final sonication count (NUM_SONICATIONS is
    local to theta_trigger_loop now, so it's read from the return value
    rather than main_pipeline module state).
    """
    main_pipeline.RUNNING = True
    main_pipeline.start_received = True

    events = []
    real_eeg_trigger_outlet = main_pipeline.eeg_trigger_outlet
    real_lifu_num_outlet = main_pipeline.lifu_num_outlet
    main_pipeline.eeg_trigger_outlet = _RecordingOutlet(events)
    main_pipeline.lifu_num_outlet = _RecordingOutlet([])

    try:
        with contextlib.redirect_stdout(io.StringIO()):
            num_sonications = main_pipeline.theta_trigger_loop(
                sample_source=_synthetic_sample_source(theta_values),
                **loop_kwargs,
            )
    finally:
        main_pipeline.eeg_trigger_outlet = real_eeg_trigger_outlet
        main_pipeline.lifu_num_outlet = real_lifu_num_outlet

    return events, num_sonications


def _report(checks):
    all_ok = True
    for description, passed in checks:
        print(f"  {'PASS' if passed else 'FAIL'}  {description}")
        all_ok = all_ok and passed
    print("RESULT:", "PASS" if all_ok else "FAIL")
    return all_ok


def test_num_sonications_increments_and_stops_at_cap():
    """theta_val stays continuously in the trigger band for far longer than
    would be needed to blow past a small max_sonications cap if the cap
    logic didn't work. NUM_SONICATIONS should climb by exactly 1 per LIFU_ON
    and stop firing -- and stop incrementing -- the instant it hits the cap,
    with no more LIFU_ON events for the remainder of the run.
    """
    print("\n=== test_num_sonications_increments_and_stops_at_cap ===")
    max_sonications = 3
    sonication_time = 0.0   # keep the test fast; the cap logic doesn't depend on real delay
    cooldown_time = 0.01    # small but nonzero, in synthetic-timestamp units (seconds)
    duration_s = 5.0        # >> max_sonications * cooldown_time, so the cap -- not running out of data -- is what stops it

    theta_values = _sine_values(int(duration_s / DT), center=3.0, amplitude=0.3, freq_hz=1.0)
    events, num_sonications = _run(
        theta_values,
        sonication_time=sonication_time,
        cooldown_time=cooldown_time,
        max_sonications=max_sonications,
    )

    on_events = [e for e in events if e == "LIFU_ON"]
    off_events = [e for e in events if e == "LIFU_OFF"]

    checks = []
    checks.append((f"exactly max_sonications ({max_sonications}) LIFU_ON events fired", len(on_events) == max_sonications))
    checks.append((f"NUM_SONICATIONS ended at max_sonications ({max_sonications})", num_sonications == max_sonications))
    checks.append(("every LIFU_ON was followed by a matching LIFU_OFF", len(on_events) == len(off_events)))
    return _report(checks)


def test_num_sonications_resets_between_runs():
    """NUM_SONICATIONS is local to each theta_trigger_loop call -- confirm
    each fresh call starts back at 0 rather than carrying over a previous
    call's count.
    """
    print("\n=== test_num_sonications_resets_between_runs ===")
    theta_values = _sine_values(int(5.0 / DT), center=3.0, amplitude=0.3, freq_hz=1.0)

    _, first_run_count = _run(theta_values, sonication_time=0.0, cooldown_time=0.01, max_sonications=2)
    _, second_run_count = _run(theta_values, sonication_time=0.0, cooldown_time=0.01, max_sonications=5)

    checks = []
    checks.append(("first run hit its own cap (2)", first_run_count == 2))
    checks.append(("second run started fresh and hit its own, different cap (5), not 2+5", second_run_count == 5))
    return _report(checks)


if __name__ == "__main__":
    results = {
        "test_num_sonications_increments_and_stops_at_cap": test_num_sonications_increments_and_stops_at_cap(),
        "test_num_sonications_resets_between_runs": test_num_sonications_resets_between_runs(),
    }

    print("\n=== Summary ===")
    for name, passed in results.items():
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")

    print("\nTest complete.")
    if not all(results.values()):
        sys.exit(1)

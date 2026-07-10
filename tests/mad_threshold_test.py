"""
Verifies that main_pipeline.theta_trigger_loop's MAD-based artifact rejection
(z = |theta_val - median| / MAD, compared against mad_threshold) actually
governs which samples get treated as artifacts, via the mad_threshold keyword
argument added to theta_trigger_loop -- not a value hardcoded in the file.

Strategy: build a smooth, low-amplitude baseline (so its own rolling
median/MAD is tiny and stable, and the baseline itself never crosses
THETA_THRESHOLD_Z), then splice in a single large spike sample at a known
buffer size. The spike's z-score relative to the baseline's buffer is fixed
by construction, so a mad_threshold below that z should reject the spike as
an artifact (no LIFU_ON, sample excluded from the buffer) and a mad_threshold
above it should accept the same spike and let it trigger -- proving the
*parameter*, not a hardcoded constant, decides the outcome.

Usage:
    python tests/mad_threshold_test.py
"""
from __future__ import annotations

import contextlib
import io
import math
import sys
import types
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# Stub out the openlifu hardware stack so this test can run without those
# bindings installed -- same approach as the other tests here.
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

# Baseline: smooth, low-amplitude sine centered well below THETA_THRESHOLD_Z
# (1.5) and INITIAL_CUTOFF (50.0), so it never triggers or gets excluded by
# initial_cutoff on its own -- only the spliced-in spike is meant to.
BASELINE_CENTER = 0.5
BASELINE_AMPLITUDE = 0.05
BUFFER_SIZE = 300   # buffer is exactly full (== BUFFER_SIZE) right when the spike lands
SPIKE_INDEX = 300   # first sample fed once the buffer holds exactly BUFFER_SIZE baseline values
SPIKE_VALUE = 2.0   # comfortably above THETA_THRESHOLD_Z (1.5), so it would trigger if accepted
SEQUENCE_LENGTH = 360


def _baseline_sequence(n):
    return [BASELINE_CENTER + BASELINE_AMPLITUDE * math.sin(2 * math.pi * 1.0 * (i * DT)) for i in range(n)]


def _spike_z_score():
    """The exact z-score SPIKE_VALUE will have against the buffer at
    SPIKE_INDEX, computed the same way theta_trigger_loop does (median/MAD
    of the buffer), so tests can pick mad_threshold values that straddle it.
    """
    arr = np.array(_baseline_sequence(BUFFER_SIZE))
    median = np.median(arr)
    mad = np.median(np.abs(arr - median)) + 1e-6
    return abs(SPIKE_VALUE - median) / mad


SPIKE_Z = _spike_z_score()
MAD_THRESHOLD_STRICT = SPIKE_Z - 10   # rejects the spike (z > threshold)
MAD_THRESHOLD_LOOSE = SPIKE_Z + 10    # accepts the spike (z <= threshold)
assert MAD_THRESHOLD_STRICT > 0, "test's synthetic spike/baseline no longer straddles a positive MAD threshold"


class _RecordingOutlet:
    def __init__(self, events):
        self._events = events

    def push_sample(self, sample, *args, **kwargs):
        self._events.append(sample[0])


def _run(theta_values, **loop_kwargs):
    """Runs the real main_pipeline.theta_trigger_loop over theta_values
    (paired with ts = i * DT), sonication enabled from the start, both
    outlets swapped for recorders. Returns (events, num_sonications): the
    ordered list of markers pushed to eeg_trigger_outlet, and the loop's own
    final sonication count (NUM_SONICATIONS is local to theta_trigger_loop
    now, so it's read from the return value rather than main_pipeline module
    state).
    """
    main_pipeline.RUNNING = True
    main_pipeline.sonication_enabled = True

    events = []
    real_eeg_trigger_outlet = main_pipeline.eeg_trigger_outlet
    real_lifu_num_outlet = main_pipeline.lifu_num_outlet
    main_pipeline.eeg_trigger_outlet = _RecordingOutlet(events)
    main_pipeline.lifu_num_outlet = _RecordingOutlet([])

    def sample_source():
        for i, theta_val in enumerate(theta_values):
            yield theta_val, i * DT

    try:
        with contextlib.redirect_stdout(io.StringIO()):
            num_sonications = main_pipeline.theta_trigger_loop(sample_source=sample_source(), **loop_kwargs)
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


def test_strict_mad_threshold_rejects_the_spike():
    """mad_threshold below the spike's actual z-score should reject it as an
    artifact: no LIFU_ON, even though SPIKE_VALUE (2.0) alone would clear
    THETA_THRESHOLD_Z (1.5), sonication is enabled, and cooldown has elapsed.
    """
    print(f"\n=== test_strict_mad_threshold_rejects_the_spike (spike z={SPIKE_Z:.1f}, threshold={MAD_THRESHOLD_STRICT:.1f}) ===")
    theta_values = _baseline_sequence(SEQUENCE_LENGTH)
    theta_values[SPIKE_INDEX] = SPIKE_VALUE

    events, num_sonications = _run(
        theta_values,
        mad_threshold=MAD_THRESHOLD_STRICT,
        buffer_size=BUFFER_SIZE,
        cooldown_time=0.01,
        sonication_time=0.0,
    )

    checks = [
        ("no LIFU_ON fired (spike correctly rejected as an artifact)", "LIFU_ON" not in events),
        ("NUM_SONICATIONS stayed at 0", num_sonications == 0),
    ]
    return _report(checks)


def test_loose_mad_threshold_accepts_the_spike():
    """The identical spike, with mad_threshold above its z-score, should be
    accepted as a genuine in-band sample and trigger exactly one LIFU_ON --
    proving the earlier rejection was governed by the threshold parameter,
    not some other property of the spike.
    """
    print(f"\n=== test_loose_mad_threshold_accepts_the_spike (spike z={SPIKE_Z:.1f}, threshold={MAD_THRESHOLD_LOOSE:.1f}) ===")
    theta_values = _baseline_sequence(SEQUENCE_LENGTH)
    theta_values[SPIKE_INDEX] = SPIKE_VALUE

    events, num_sonications = _run(
        theta_values,
        mad_threshold=MAD_THRESHOLD_LOOSE,
        buffer_size=BUFFER_SIZE,
        cooldown_time=0.01,
        sonication_time=0.0,
    )

    checks = [
        ("exactly one LIFU_ON fired", events.count("LIFU_ON") == 1),
        ("NUM_SONICATIONS incremented to 1", num_sonications == 1),
    ]
    return _report(checks)


def test_rejected_spike_is_excluded_from_the_buffer():
    """A rejected artifact must not get folded into the rolling buffer --
    otherwise it would skew the median/MAD that later samples are judged
    against. Confirmed by comparing a run with the spike (under the strict
    threshold that rejects it) against a control run where that same index
    just continues the clean baseline: if the spike is truly excluded, the
    two runs must produce identical events.
    """
    print("\n=== test_rejected_spike_is_excluded_from_the_buffer ===")
    control_values = _baseline_sequence(SEQUENCE_LENGTH)
    spiked_values = list(control_values)
    spiked_values[SPIKE_INDEX] = SPIKE_VALUE

    control_events, _ = _run(
        control_values, mad_threshold=MAD_THRESHOLD_STRICT, buffer_size=BUFFER_SIZE,
        cooldown_time=0.01, sonication_time=0.0,
    )
    spiked_events, _ = _run(
        spiked_values, mad_threshold=MAD_THRESHOLD_STRICT, buffer_size=BUFFER_SIZE,
        cooldown_time=0.01, sonication_time=0.0,
    )

    checks = [
        ("no LIFU_ON in the control run (clean baseline never crosses threshold)", "LIFU_ON" not in control_events),
        ("spiked run's events match the control run exactly (rejected spike left no trace)", spiked_events == control_events),
    ]
    return _report(checks)


if __name__ == "__main__":
    results = {
        "test_strict_mad_threshold_rejects_the_spike": test_strict_mad_threshold_rejects_the_spike(),
        "test_loose_mad_threshold_accepts_the_spike": test_loose_mad_threshold_accepts_the_spike(),
        "test_rejected_spike_is_excluded_from_the_buffer": test_rejected_spike_is_excluded_from_the_buffer(),
    }

    print("\n=== Summary ===")
    for name, passed in results.items():
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")

    print("\nTest complete.")
    if not all(results.values()):
        sys.exit(1)

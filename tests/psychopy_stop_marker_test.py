"""
Verifies the full STOP_EXPERIMENT round trip between N-back_lastrun.py and
main_pipeline.py's listen_for_start_stop().

Two things are checked, because the round trip has two independent halves
and the actual bug was entirely in one of them:

1. The producer side: N-back_lastrun.py's source actually pushes a
   "STOP_EXPERIMENT" marker when it detects the -1.0 stop sentinel from
   main_pipeline.py's stop_psychopy(). This is a source-text check rather
   than a live run, since driving the real PsychoPy script needs an actual
   visual window/keyboard. This is the half that was ACTUALLY BROKEN:
   N-back_lastrun.py used to just set thisExp.status = FINISHED locally on
   the -1.0 sentinel and never told main_pipeline.py it had stopped.

2. The consumer side: main_pipeline.py's listen_for_start_stop() actually
   flips psychopy_running back to False when a "STOP_EXPERIMENT" marker
   arrives over the real "PsychoPyMarkers" LSL stream. This half was
   already correct before the fix -- included here so the round trip has
   end-to-end coverage, since other tests in this suite
   (theta_lifu_validation_test.py, num_sonications_test.py,
   mad_threshold_test.py) deliberately bypass listen_for_start_stop() and
   set main_pipeline.psychopy_running directly, mirroring its effect
   without any LSL, which is exactly why this side of the contract went
   uncovered.

Usage:
    pytest tests/psychopy_stop_marker_test.py -v
"""
from __future__ import annotations

import math
import queue
import re
import sys
import threading
import time
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# main_pipeline imports the openlifu hardware stack purely to construct
# objects this test never touches. Stub those out so this test can run
# without the hardware bindings installed -- same approach as the other
# tests in this directory.
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
from pylsl import StreamInfo, StreamOutlet  # noqa: E402

LASTRUN_PATH = REPO_ROOT / "n-back-task-with-visual-stimuli" / "N-back_lastrun.py"


class _RecordingOutlet:
    """Stand-in for main_pipeline.eeg_trigger_outlet -- records every
    push_sample(...) call instead of transmitting over LSL."""

    def __init__(self, events):
        self._events = events

    def push_sample(self, sample, *args, **kwargs):
        self._events.append(sample[0])


@pytest.fixture(autouse=True)
def _reset_main_pipeline_globals():
    """main_pipeline.RUNNING/psychopy_running/baseline_ready are module-level
    globals shared across every test in this suite (see num_sonications_test.py,
    mad_threshold_test.py) -- reset them before each test, and force RUNNING
    False afterward so a listener/loop thread from this test can't keep
    spinning into the next one."""
    main_pipeline.RUNNING = True
    main_pipeline.psychopy_running = False
    main_pipeline.baseline_ready = False
    yield
    main_pipeline.RUNNING = False


@pytest.fixture
def recorded_events():
    """Swaps main_pipeline.eeg_trigger_outlet/lifu_num_outlet for in-memory
    recorders for the duration of one test, and always restores the real
    ones afterward -- even if the test fails."""
    events = []
    real_eeg_trigger_outlet = main_pipeline.eeg_trigger_outlet
    real_lifu_num_outlet = main_pipeline.lifu_num_outlet
    main_pipeline.eeg_trigger_outlet = _RecordingOutlet(events)
    main_pipeline.lifu_num_outlet = _RecordingOutlet([])
    yield events
    main_pipeline.eeg_trigger_outlet = real_eeg_trigger_outlet
    main_pipeline.lifu_num_outlet = real_lifu_num_outlet


def _push_until(outlet, sample, predicate, timeout=10.0, interval=0.2):
    """Pushes `sample` repeatedly until `predicate()` is true. A single push
    right after the listener thread starts can race the StreamInlet's
    connection handshake and get dropped (the inlet isn't fully connected
    yet), so this resends instead of relying on a single push landing."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        outlet.push_sample(sample)
        time.sleep(interval)
    return predicate()


def test_lastrun_script_pushes_stop_experiment_on_sentinel():
    """N-back_lastrun.py must push "STOP_EXPERIMENT" in the same breath as
    setting thisExp.status = FINISHED in response to the -1.0 stop sentinel
    -- not just set the status locally. This is a source-text check (not a
    live PsychoPy run, which needs a real window/keyboard); it fails on the
    pre-fix version of the file, where these -1.0 blocks only ever set
    thisExp.status = FINISHED and never told main_pipeline.py anything.
    """
    source = LASTRUN_PATH.read_text(encoding="utf-8")

    stop_experiment_push = 'marker_outlet.push_sample(["STOP_EXPERIMENT"])'
    occurrences = source.count(stop_experiment_push)
    assert occurrences >= 2, (
        f"expected at least 2 occurrences of {stop_experiment_push!r} in "
        f"{LASTRUN_PATH.name} (main trial loop + thank-you screen), found "
        f"{occurrences} -- the -1.0 sentinel handling may have regressed "
        "back to only setting thisExp.status = FINISHED without telling "
        "main_pipeline.py the experiment stopped"
    )

    # Each push must sit directly alongside the -1.0 check it belongs to,
    # not somewhere unrelated in the file.
    pattern = re.compile(
        r'(?:sample\[0\]|_stop_sample\[0\]) == -1\.0:\s*\n\s*'
        r'marker_outlet\.push_sample\(\["STOP_EXPERIMENT"\]\)\s*\n\s*'
        r'thisExp\.status = FINISHED'
    )
    matches = pattern.findall(source)
    assert len(matches) >= 2, (
        f"expected the STOP_EXPERIMENT push to immediately precede "
        f"thisExp.status = FINISHED within the -1.0 sentinel check, in at "
        f"least 2 places; found {len(matches)} such blocks in "
        f"{LASTRUN_PATH.name}"
    )


def test_stop_experiment_marker_resets_psychopy_running(recorded_events):
    """trial_start -> psychopy_running True; STOP_EXPERIMENT -> False again."""
    events = recorded_events

    # A real local "PsychoPyMarkers" outlet, exactly like the one
    # N-back_lastrun.py creates -- this is what listen_for_start_stop()
    # resolves and reads via LSL, not a mock.
    marker_info = StreamInfo("PsychoPyMarkers", "Markers", 1, 0, "string", "test_psychopy_markers")
    marker_outlet = StreamOutlet(marker_info)

    listener_thread = threading.Thread(target=main_pipeline.listen_for_start_stop, daemon=True)

    try:
        listener_thread.start()

        assert _push_until(
            marker_outlet, ["trial_start"], lambda: main_pipeline.psychopy_running is True
        ), (
            "psychopy_running never became True after a trial_start marker"
        )
        assert "START_EXPERIMENT_RECEIVED" in events, (
            f"expected START_EXPERIMENT_RECEIVED in {events}"
        )

        assert _push_until(
            marker_outlet, ["STOP_EXPERIMENT"], lambda: main_pipeline.psychopy_running is False
        ), (
            "psychopy_running never went back to False after a STOP_EXPERIMENT "
            "marker -- this is the bug: without N-back_lastrun.py pushing this "
            "marker, listen_for_start_stop() never hears that the experiment "
            "stopped"
        )
        assert "STOP_EXPERIMENT_RECEIVED" in events, (
            f"expected STOP_EXPERIMENT_RECEIVED in {events}"
        )

    finally:
        main_pipeline.RUNNING = False
        listener_thread.join(timeout=2.0)


def _queue_sample_source(q):
    """Yields (theta_val, ts) pairs pulled from `q`, one at a time, blocking
    until each is available. Lets the test hand theta_trigger_loop samples
    at precisely chosen moments (e.g. "only after psychopy_running has
    actually flipped False"), instead of racing real time. A `None` item
    ends the generator, matching how a live LSL sample_source ends when
    RUNNING goes False."""
    while True:
        item = q.get()
        if item is None:
            return
        yield item


def _wait_until(predicate, timeout=10.0, interval=0.05):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


def _in_band_sine_samples(n, start_ts, dt=0.01, center=3.0, amplitude=0.3, freq_hz=1.0):
    """n continuously in-band (theta_val > THETA_THRESHOLD_Z=1.5 throughout,
    since range is [2.7, 3.3]) samples of low, consistent variance. Used for
    BOTH baseline collection and the trigger check itself -- same trick
    num_sonications_test.py relies on: a value that jumped straight from a
    flat near-zero baseline to 3.0 would get rejected by the rolling
    MAD-based artifact filter as an outlier, not evaluated against the
    psychopy_running gate this test actually cares about."""
    return [
        (center + amplitude * math.sin(2 * math.pi * freq_hz * i * dt), start_ts + i * dt)
        for i in range(n)
    ]


def test_theta_crossing_after_stop_experiment_does_not_sonicate(recorded_events):
    """Edge case: a theta threshold crossing that arrives AFTER psychopy_running
    has been reset to False (via a real STOP_EXPERIMENT marker) must NOT
    trigger a LIFU_ON marker, even though the value itself is well within
    the trigger band and baseline/cooldown/cap gating would otherwise allow
    it. This is the scenario the STOP_EXPERIMENT fix exists to guarantee: a
    stale in-flight theta sample must not sonicate someone after the
    experiment has already ended.

    Sequenced as one lifecycle rather than two separate tests so the second
    half is a genuine regression check and not a tautology: the same kind
    of in-band sample is shown to actually sonicate *before* the stop, and
    then shown to be suppressed *after* it, against the real
    listen_for_start_stop() listener (not a hand-set flag).
    """
    events = recorded_events

    marker_info = StreamInfo("PsychoPyMarkers", "Markers", 1, 0, "string", "test_psychopy_markers_2")
    marker_outlet = StreamOutlet(marker_info)
    listener_thread = threading.Thread(target=main_pipeline.listen_for_start_stop, daemon=True)

    sample_queue: queue.Queue = queue.Queue()
    loop_result: dict = {}

    def _run_loop():
        loop_result["num_sonications"] = main_pipeline.theta_trigger_loop(
            sample_source=_queue_sample_source(sample_queue),
            sonication_time=0.0,
            cooldown_time=1.0,
            max_sonications=10,
        )

    loop_thread = threading.Thread(target=_run_loop, daemon=True)

    try:
        listener_thread.start()
        loop_thread.start()

        # 1. Start the experiment for real, over LSL.
        assert _push_until(
            marker_outlet, ["trial_start"], lambda: main_pipeline.psychopy_running is True
        ), "psychopy_running never became True after trial_start"

        # 2. Feed just enough continuously in-band samples to fill the
        #    baseline buffer and let one trigger fire -- deliberately not
        #    more than that, so NUM_SONICATIONS is still well under
        #    max_sonications when we get to step 5 (otherwise a "no more
        #    LIFU_ON" result there could just mean "hit the cap", not
        #    "psychopy_running gated it", which is the thing under test).
        pre_stop_samples = _in_band_sine_samples(main_pipeline.BUFFER_COLLECTION_SIZE + 5, start_ts=0.0)
        for sample in pre_stop_samples:
            sample_queue.put(sample)
        last_pre_stop_ts = pre_stop_samples[-1][1]

        assert _wait_until(lambda: main_pipeline.baseline_ready, timeout=10.0), (
            "baseline never became ready"
        )

        # 3. Positive control: confirms the trigger band itself is live
        #    while psychopy_running is True. If this never fires, the "no
        #    marker after stop" result below would be meaningless -- it'd
        #    just mean this signal never triggers at all, not that the
        #    psychopy_running gate is doing its job.
        assert _wait_until(lambda: "LIFU_ON" in events, timeout=5.0), (
            "sanity check failed: a continuously in-band theta signal while "
            "psychopy_running was True never produced a LIFU_ON marker -- "
            "the test fixture itself isn't exercising the trigger band"
        )
        pre_stop_lifu_on_count = events.count("LIFU_ON")
        assert pre_stop_lifu_on_count < 5, (
            "positive control fired enough times to hit max_sonications already -- "
            "tighten cooldown_time/sample count so step 5 isn't confounded by the cap"
        )

        # 4. Stop the experiment for real, over LSL -- the actual fix under test.
        assert _push_until(
            marker_outlet, ["STOP_EXPERIMENT"], lambda: main_pipeline.psychopy_running is False
        ), "psychopy_running never went back to False after STOP_EXPERIMENT"

        # 5. Only now, after the stop has actually landed, feed a fresh run
        #    of the same in-band signal, well past cooldown_time (1.0s in
        #    synthetic-timestamp units, vs. a >10s gap here) so cooldown
        #    gating isn't what's being tested -- psychopy_running gating is.
        post_stop_samples = _in_band_sine_samples(50, start_ts=last_pre_stop_ts + 10.0)
        for sample in post_stop_samples:
            sample_queue.put(sample)
        last_post_stop_ts = post_stop_samples[-1][1]

        # Drain: push one more sample past this point so we know
        # theta_trigger_loop has actually processed everything queued above
        # (it processes samples strictly in order), rather than guessing
        # with a fixed sleep.
        sample_queue.put((1.0, last_post_stop_ts + 0.01))
        assert _wait_until(
            lambda: sample_queue.empty(), timeout=5.0
        ), "theta_trigger_loop never drained the post-stop samples"
        time.sleep(0.2)  # let the loop finish acting on the last item it dequeued

        assert events.count("LIFU_ON") == pre_stop_lifu_on_count, (
            f"a LIFU_ON marker was sent for a theta crossing that arrived "
            f"AFTER psychopy_running was reset to False by STOP_EXPERIMENT "
            f"-- events={events}"
        )

    finally:
        sample_queue.put(None)
        main_pipeline.RUNNING = False
        loop_thread.join(timeout=2.0)
        listener_thread.join(timeout=2.0)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))

from __future__ import annotations


import logging
import math
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path


if os.name == 'nt':
    import msvcrt
else:
    import select


import numpy as np
from pylsl import StreamInlet, resolve_byprop, StreamInfo, StreamOutlet


import gpype as gp


from openlifu.bf.pulse import Pulse
from openlifu.bf.sequence import Sequence
from openlifu.db import Database
from openlifu.geo import Point
from openlifu.io.LIFUInterface import LIFUInterface
from openlifu.plan.solution import Solution


# ============================================================
# Run configuration (paths, output dirs, mode flags)
# ============================================================

# name convention
name_and_trial = "no_run"

# all XDF output goes here (written by LabRecorder, see start_lab_recorder())
XDF_DIR = Path("xdf_data")
XDF_DIR.mkdir(exist_ok=True)

#global variables for threads
RUNNING = True

# Set OW_HARDWARE_ENABLED=1 for NO GUI (python sonication)
HARDWARE_ENABLED = bool(os.environ.get("OW_HARDWARE_ENABLED"))

# Set OW_SHAM_RUN=1 for a sham (placebo) run --> run never pressed through slicer
SHAM_RUN = bool(os.environ.get("OW_SHAM_RUN"))


# ============================================================
# Logging
# ============================================================

# logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


# ============================================================
# Generic subprocess/cleanup utilities
# ============================================================

# Every subprocess we manage ourselves (LabRecorder, PsychoPy,
# lsl_visualizer.py) is launched in its own process group on Windows so it
# doesn't receive Ctrl+C directly from the console -- otherwise a raw
# KeyboardInterrupt can leave e.g. lsl_visualizer.py's Qt event loop in an
# undefined state instead of going through our own clean stop_*()/terminate()
# calls below, which are what actually shut each one down.
_SUBPROCESS_KWARGS = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {}


def _cleanup_step(description: str, fn, *args) -> None:
    """Runs one shutdown step in isolation. If it raises -- including a
    second KeyboardInterrupt from an impatient extra Ctrl+C while a slow
    step (e.g. p.stop()) is still blocking -- this logs it and lets the
    remaining cleanup steps still run, instead of one failure silently
    skipping everything after it in the same finally block.
    """
    try:
        fn(*args)
    except BaseException as e:
        logger.warning("Cleanup step %r failed: %s", description, e)


def _terminate_proc(proc: subprocess.Popen | None, timeout: float = 5.0) -> None:
    """Terminates a subprocess we launched (PsychoPy, lsl_visualizer.py),
    falling back to kill() if it doesn't exit within `timeout` seconds.
    """
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()


# ============================================================
# LSL outlets (created at import time)
# ============================================================

# Sending markers to EEG
eeg_trigger_info = StreamInfo('EEG_LIFU_events', 'Markers', 1, 0, 'string')
eeg_trigger_outlet = StreamOutlet(eeg_trigger_info)
logger.info("LIFU to PsychoPy LSL outlet created.")


#sending markers to psychopy
lifu_num_info = StreamInfo('PsychoPy_numeric', 'Markers', 1, 0, 'float32')
lifu_num_outlet = StreamOutlet(lifu_num_info)
logger.info("LIFU to PsychoPy LSL outlet created.")


# ============================================================
# LabRecorder automation
# ============================================================

# Set OW_NO_LABRECORDER=1 to skip this and drive LabRecorder manually instead.
def _find_labrecorder_exe() -> Path | None:
    """Auto-discovers LabRecorder.exe under this repo instead of hardcoding
    a version-specific install path, so upgrading LabRecorder (unzipping a
    new LabRecorder-X.Y.Z-Win_amd64 folder here) doesn't require editing
    this file. Picks the most recently modified match if more than one
    install is found. Set OW_LABRECORDER_EXE if it lives somewhere else
    entirely (e.g. outside this repo).
    """
    matches = sorted(
        Path(__file__).resolve().parent.glob("LabRecorder*/LabRecorder.exe"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


_labrecorder_exe_override = os.environ.get("OW_LABRECORDER_EXE")
LABRECORDER_EXE = Path(_labrecorder_exe_override) if _labrecorder_exe_override else _find_labrecorder_exe()
LABRECORDER_RCS_HOST = "127.0.0.1"
LABRECORDER_RCS_PORT = 22345
SESSION_LABEL = os.environ.get("OW_SESSION", "1")


def _connect_labrecorder_rcs(timeout: float) -> socket.socket | None:
    """Repeatedly tries to open LabRecorder's remote-control TCP socket
    until it succeeds or `timeout` seconds pass. Returns None on timeout.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            return socket.create_connection((LABRECORDER_RCS_HOST, LABRECORDER_RCS_PORT), timeout=1.0)
        except OSError:
            time.sleep(0.5)
    return None


_LABRECORDER_CFG_MARKER_BEGIN = "; --- OW_closedloopLIFU managed settings (auto-generated -- edits here are overwritten) ---"
_LABRECORDER_CFG_MARKER_END = "; --- end OW_closedloopLIFU managed settings ---"
_LABRECORDER_REQUIRED_STREAM_NAMES = ["EEG_gpype", "EEG_LIFU_events", "PsychoPy_numeric", "PsychoPyMarkers"]


def _ensure_labrecorder_cfg() -> None:
    """Writes StudyRoot/RequiredStreams/RCSEnabled directly into
    LabRecorder.cfg (next to LABRECORDER_EXE) before launching it.

    LabRecorder.cfg ships with every setting (StudyRoot, RequiredStreams,
    etc.) commented out as documentation/examples. Its Config dialog's
    "Save" does not write back into this file: after repeatedly setting
    Study Root and Required Streams through the GUI and saving, this file
    on disk still only ever had RCSEnabled/RCSPort active -- so those
    settings never actually took effect on the next launch, and every
    launch fell back to LabRecorder's hardcoded default
    (Documents/CurrentStudy/) with no required streams. This writes them
    directly into the file LabRecorder actually loads on startup instead of
    relying on the GUI to persist them.
    """
    cfg_path = LABRECORDER_EXE.parent / "LabRecorder.cfg"
    hostname = socket.gethostname()
    required_streams = ",".join(
        f'"{name} ({hostname})"' for name in _LABRECORDER_REQUIRED_STREAM_NAMES
    )
    managed_block = "\n".join([
        _LABRECORDER_CFG_MARKER_BEGIN,
        f"StudyRoot={XDF_DIR.resolve().as_posix()}",
        f"RequiredStreams={required_streams}",
        "RCSEnabled=1",
        f"RCSPort={LABRECORDER_RCS_PORT}",
        _LABRECORDER_CFG_MARKER_END,
    ])

    existing = cfg_path.read_text() if cfg_path.exists() else ""
    if _LABRECORDER_CFG_MARKER_BEGIN in existing:
        start = existing.index(_LABRECORDER_CFG_MARKER_BEGIN)
        end = existing.index(_LABRECORDER_CFG_MARKER_END) + len(_LABRECORDER_CFG_MARKER_END)
        existing = existing[:start] + existing[end:]
    cfg_path.write_text(existing.rstrip("\n") + "\n\n" + managed_block + "\n")
    logger.info("Wrote LabRecorder.cfg (StudyRoot=%s).", XDF_DIR.resolve())


def start_lab_recorder() -> tuple[subprocess.Popen | None, bool]:
    """Launches LabRecorder (reusing an already-running instance if its RCS
    port is already open) and starts an XDF recording of every stream
    matching its configured Required Streams list. _ensure_labrecorder_cfg()
    writes that config itself -- no manual GUI setup required.

    Returns (proc, started). The RCS socket used here is closed again before
    returning -- it is not held open for the rest of the session, since a
    long recording run risks it going stale/dropped by the time
    stop_lab_recorder() would otherwise try to reuse it to send "stop".
    stop_lab_recorder() instead opens its own fresh connection.
    """
    if os.environ.get("OW_NO_LABRECORDER"):
        logger.info("OW_NO_LABRECORDER set; not auto-launching LabRecorder.")
        return None, False

    proc = None
    sock = _connect_labrecorder_rcs(timeout=1.0)
    if sock is None:
        if LABRECORDER_EXE is None or not LABRECORDER_EXE.exists():
            logger.warning(
                "LabRecorder.exe not found under the repo (set OW_LABRECORDER_EXE); "
                "skipping XDF recording. Looked for: %s",
                LABRECORDER_EXE,
            )
            return None, False
        _ensure_labrecorder_cfg()
        proc = subprocess.Popen(
            [str(LABRECORDER_EXE)], cwd=str(LABRECORDER_EXE.parent), **_SUBPROCESS_KWARGS
        )
        logger.info("Launched LabRecorder (pid=%s).", proc.pid)
        sock = _connect_labrecorder_rcs(timeout=20.0)
        if sock is None:
            logger.warning(
                "LabRecorder did not open its remote-control port (%s:%d). "
                "Is 'EnableRCS' checked in its Config? Falling back to manual recording.",
                LABRECORDER_RCS_HOST, LABRECORDER_RCS_PORT,
            )
            return proc, False

    def send(cmd: str) -> None:
        sock.sendall((cmd + "\n").encode("utf-8"))

    try:
        send("update")
        time.sleep(2.0)  # let LabRecorder finish its network stream scan
        send("select all")
        # Deliberately omits {template:...}: per LabRecorder's RCS docs, the
        # "template" key unselects BIDS mode as a side effect, which broke
        # the sub-%p/ses-%s/eeg/... path construction mid-command. BIDS mode
        # + that template are configured once in the GUI instead -- see
        # "Filename template" in readme.md -- so this only ever fills in the
        # placeholders in the template LabRecorder already has.
        send(
            "filename {root:%s} {participant:%s} {session:%s} {task:%s}"
            % (XDF_DIR.resolve(), name_and_trial, SESSION_LABEL, name_and_trial)
        )
        send("start")
    except OSError as e:
        logger.warning("Failed to start LabRecorder recording over RCS: %s", e)
        sock.close()
        return proc, False
    finally:
        sock.close()

    logger.info("LabRecorder recording started (XDF -> %s).", XDF_DIR.resolve())
    return proc, True


def stop_lab_recorder(proc: subprocess.Popen | None, started: bool) -> None:
    """Stops the recording started by start_lab_recorder(), over a freshly
    opened RCS connection (see start_lab_recorder()'s docstring for why this
    doesn't reuse the original one). Leaves the LabRecorder process itself
    running (even if we launched it) so the recorded file can be inspected
    in the GUI.
    """
    if not started:
        return
    sock = _connect_labrecorder_rcs(timeout=5.0)
    if sock is None:
        logger.warning(
            "Could not reach LabRecorder's remote-control port (%s:%d) to stop recording -- "
            "stop it manually.", LABRECORDER_RCS_HOST, LABRECORDER_RCS_PORT,
        )
        return
    try:
        sock.sendall(b"stop\n")
        logger.info("Sent stop command to LabRecorder.")
    except OSError as e:
        logger.warning("Failed to send stop command to LabRecorder: %s", e)
    finally:
        sock.close()


# ============================================================
# PsychoPy automation
# ============================================================

# PsychoPy task automation. Defaults to the 2-back task since that's the one
# paired with LIFU triggering. Set OW_PSYCHOPY_SCRIPT to point at a different
# Builder-exported script (e.g. stroop/stroop_lastrun.py) instead, or
# OW_NO_PSYCHOPY=1 to skip auto-launching it and start the task by hand.
#
# PsychoPy lives in its own Python install, separate from this script's
# interpreter (which doesn't have the `psychopy` package) -- so it can't be
# launched with sys.executable. Override OW_PSYCHOPY_PYTHON if this moves.
PSYCHOPY_SCRIPT = Path(os.environ.get(
    "OW_PSYCHOPY_SCRIPT",
    r"C:\Users\jshin\OW_closedloopLIFU\n-back-task-with-visual-stimuli\N-back_lastrun.py",
))
PSYCHOPY_PYTHON = Path(os.environ.get("OW_PSYCHOPY_PYTHON", r"C:\Users\jshin\python.exe"))


def start_psychopy() -> subprocess.Popen | None:
    """Launches the PsychoPy task as a subprocess with OW_PARTICIPANT set to
    name_and_trial, which the small patch near the top of
    N-back_lastrun.py/stroop_lastrun.py reads to pre-fill the participant
    field. The task's own info dialog still opens (so session number etc.
    can still be checked/adjusted) -- it just no longer needs the
    participant name typed in by hand.
    """
    if os.environ.get("OW_NO_PSYCHOPY"):
        logger.info("OW_NO_PSYCHOPY set; not auto-launching the PsychoPy task.")
        return None
    if not PSYCHOPY_SCRIPT.exists():
        logger.warning("PsychoPy script not found at %s; start it manually.", PSYCHOPY_SCRIPT)
        return None
    if not PSYCHOPY_PYTHON.exists():
        logger.warning(
            "PsychoPy Python not found at %s (set OW_PSYCHOPY_PYTHON); start the task manually.",
            PSYCHOPY_PYTHON,
        )
        return None

    env = dict(os.environ, OW_PARTICIPANT=name_and_trial)
    proc = subprocess.Popen(
        [str(PSYCHOPY_PYTHON), str(PSYCHOPY_SCRIPT)],
        cwd=str(PSYCHOPY_SCRIPT.parent),
        env=env,
        **_SUBPROCESS_KWARGS,
    )
    logger.info("Launched PsychoPy task %s (pid=%s).", PSYCHOPY_SCRIPT.name, proc.pid)
    return proc


PSYCHOPY_STOP_SENTINEL = -1.0  # never used for a real LIFU_ON/OFF tick (those are 1.0/0.0)


def stop_psychopy(proc: subprocess.Popen | None) -> None:
    """Asks the PsychoPy task to stop gracefully before falling back to a
    hard kill. Pushes PSYCHOPY_STOP_SENTINEL on lifu_num_outlet
    (PsychoPy_numeric) -- N-back_lastrun.py/stroop_lastrun.py poll that
    stream every frame and treat this value exactly like pressing Escape:
    thisExp.status is set to FINISHED, so run() returns and __main__ still
    reaches saveData() before the process exits, instead of losing that
    participant's .csv/.psydat to subprocess.terminate() mid-experiment.

    Falls back to _terminate_proc() if the process doesn't exit on its own
    within a few seconds -- e.g. it's still on the info dialog, before
    anything is polling for the sentinel yet.
    """
    if proc is None or proc.poll() is not None:
        return
    try:
        lifu_num_outlet.push_sample([PSYCHOPY_STOP_SENTINEL])
    except Exception as e:
        logger.warning("Failed to send PsychoPy stop signal over LSL: %s", e)
    try:
        proc.wait(timeout=8.0)
        logger.info("PsychoPy exited on its own after the stop signal (data saved).")
        return
    except subprocess.TimeoutExpired:
        logger.warning(
            "PsychoPy didn't exit within 8s of the stop signal (maybe still on the "
            "info dialog); forcing it closed -- its data for this run may not be saved."
        )
    _terminate_proc(proc)


# ============================================================
# Slicer remote-run automation
# ============================================================

# Slicer remote-run automation. OpenLIFUSonicationControl.py (the Slicer
# module) starts a small local TCP listener on SLICER_RUN_PORT; this sends it
# the same command as clicking its Run button. Only meaningful when
# HARDWARE_ENABLED is False -- that's the workflow where Slicer's GUI (not
# this script) holds the LIFUInterface connection and does the actual
# hardware firing off of the PsychoPy_numeric LSL markers this script emits
# (see theta_trigger_loop). Slicer must already be running with the module
# open, device connected, and an approved solution sent to hardware -- this
# only presses the Run button, it doesn't do that setup. Skipped whenever
# SHAM_RUN is set (see __main__) -- without Slicer's solution ever being
# "Run", it stays unarmed, so the LIFU_ON/OFF markers this script still
# emits normally never cause the transducer to fire.
SLICER_RUN_HOST = "127.0.0.1"
SLICER_RUN_PORT = int(os.environ.get("OW_SLICER_RUN_PORT", "18946"))


def trigger_slicer_run(timeout: float = 5.0) -> bool:
    try:
        with socket.create_connection((SLICER_RUN_HOST, SLICER_RUN_PORT), timeout=timeout) as sock:
            sock.sendall(b"run\n")
            reply = sock.recv(1024).decode("utf-8", errors="ignore").strip()
        if reply == "ok":
            logger.info("Triggered Slicer's Run button over the remote-run listener.")
            return True
        logger.warning("Slicer remote-run listener replied unexpectedly: %r", reply)
        return False
    except OSError as e:
        logger.warning(
            "Could not reach Slicer's remote-run listener (%s:%d): %s. Is Slicer running "
            "with the OpenLIFUSonicationControl module open, device connected, and solution "
            "sent to hardware? Click Run manually instead.",
            SLICER_RUN_HOST, SLICER_RUN_PORT, e,
        )
        return False


# ============================================================
# LIFU hardware init
# ============================================================

def init_hardware(
    db_path: Path | None = None,
    num_modules: int = 1,
    use_external_power_supply: bool = False,
    xInput: float = 0,
    yInput: float = 0,
    zInput: float = 50,
    frequency_kHz: float = 400,
    voltage: float = 20.0,
    duration_msec: float = 3,
    interval_msec: float = 10,
) -> tuple[LIFUInterface, Solution]:
    # Powers on and connects to the physical LIFU transducer hardware, computes the
    # beamforming delays/apodizations needed to focus ultrasound at the (x, y, z)
    # target point, and uploads that "Solution" to the device so it's ready to fire.
    # Only called when HARDWARE_ENABLED -- never on import (e.g. tests).
    peak_to_peak_voltage = voltage * 2
    if db_path is None:
        db_path = Path(r"C:\Users\jshin\Downloads\OpenLIFU-python\OpenLIFU-python\db_dvc")
    db = Database(db_path)
    arr = db.load_transducer(f"openlifu_{num_modules}x400_evt1")
    arr.sort_by_pin()

    target = Point(position=(xInput, yInput, zInput), units="mm")
    focus = target.get_position(units="mm")

    positions = arr.get_positions(units="mm")
    distances = np.sqrt(np.sum((focus - positions) ** 2, axis=1)).reshape(1, -1)

    speed_of_sound = 1500
    tof = distances * 1e-3 / speed_of_sound
    delays = tof.max() - tof
    apodizations = np.ones((1, arr.numelements()))
    logger.info("Starting LIFU Test Script...")
    interface = LIFUInterface(ext_power_supply=use_external_power_supply)
    tx_connected, hv_connected = interface.is_device_connected()

    interface.hvcontroller.turn_12v_on()
    time.sleep(0.8)

    interface.stop_monitoring()
    del interface
    interface = LIFUInterface(ext_power_supply=False)

    tx_connected, hv_connected = interface.is_device_connected()
    if not tx_connected:
        raise RuntimeError("TX not connected after 12V power-up")

    interface.hvcontroller.turn_hv_on()
    time.sleep(0.5)

    if not use_external_power_supply and not tx_connected:
        logger.warning("TX device not connected. Attempting to turn on 12V...")
        interface.hvcontroller.turn_hv_on()
        time.sleep(2)
        interface.hvcontroller.turn_12v_on()
        time.sleep(2)
        interface.stop_monitoring()
        del interface
        time.sleep(1)
        logger.info("Reinitializing LIFU interface after powering 12V...")
        interface = LIFUInterface(ext_power_supply=use_external_power_supply)
        tx_connected, hv_connected = interface.is_device_connected()

    if not use_external_power_supply:
        if hv_connected:
            logger.info(f"  HV Connected: {hv_connected}")
        else:
            raise RuntimeError("HV NOT fully connected.")
    else:
        logger.info("Using external power supply")

    if tx_connected:
        logger.info(f"  TX Connected: {tx_connected}")
        logger.info("LIFU Device fully connected.")
    else:
        raise RuntimeError("TX NOT fully connected.")

    if not interface.txdevice.ping():
        raise RuntimeError("Failed to ping the transmitter device.")

    if not use_external_power_supply and not interface.hvcontroller.ping():
        raise RuntimeError("Failed to ping the console device.")

    if not use_external_power_supply:
        try:
            console_firmware_version = interface.hvcontroller.get_version()
            logger.info(f"Console Firmware Version: {console_firmware_version}")
        except Exception as e:
            logger.error(f"Error querying console firmware version: {e}")

    try:
        tx_firmware_version = interface.txdevice.get_version()
        logger.info(f"TX Firmware Version: {tx_firmware_version}")
    except Exception as e:
        logger.error(f"Error querying TX firmware version: {e}")

    logger.info("Enumerate TX7332 chips")
    num_tx_devices = interface.txdevice.enum_tx7332_devices()
    if num_tx_devices == 0:
        raise ValueError("No TX7332 devices found.")
    elif num_tx_devices == num_modules * 2:
        logger.info(f"Number of TX7332 devices found: {num_tx_devices}")
        numelements = 32 * num_tx_devices
    else:
        raise Exception(f"Number of TX7332 devices found: {num_tx_devices} != 2x{num_modules}")

    logger.info(f'Apodizations: {apodizations}')
    logger.info(f'Delays: {delays}')

    pulse = Pulse(frequency=frequency_kHz * 1e3, duration=duration_msec * 1e-3)

    sequence = Sequence(
        pulse_interval=interval_msec * 1e-3,
        pulse_count=int(60 / (interval_msec * 1e-3)),
        pulse_train_interval=0,
        pulse_train_count=1
    )

    pin_order = np.argsort([el.pin for el in arr.elements])

    solution = Solution(
        delays=delays[:, pin_order],
        apodizations=apodizations[:, pin_order],
        transducer=arr,
        pulse=pulse,
        voltage=voltage,
        sequence=sequence
    )

    interface.set_solution(
        solution=solution,
        profile_index=1,
        profile_increment=False,
        trigger_mode="continuous"
    )

    logger.info("Beamforming solution loaded.")
    return interface, solution




# ============================================================
# g.Pype router / channel-index config
# ============================================================

# Single source of truth for the g.Pype Router wiring: run_pipeline() below
# builds `merger = gp.Router(input_channels=ROUTER_INPUT_CHANNELS, ...)` from
# this exact dict, so a channel's position in every EEG_gpype LSL sample is
# always this dict's iteration order -- reordering/renaming keys here (and
# in run_pipeline()'s merger) is reflected automatically by
# _router_channel_index() below instead of needing a hand-kept index list.
# Index 11 ("hold": the decimated + z-scored theta signal held by
# gp.Hold()) was mistaken for Smoothed Power -- that mismatch was issue #3.
# Smoothed Power is "moving_average" (index 9), which is what
# theta_trigger_loop's own median/MAD z-scoring expects as input.
ROUTER_INPUT_CHANNELS = {
    "channel_1": [0],
    "channel_2": [1],
    "channel_3": [2],
    "channel_4": [3],
    "channel_5": [4],
    "channel_6": [5],
    "channel_7": [6],
    "theta_filter": [0],
    "power": [0],
    "moving_average": [0],
    "theta_z": [0],
    "hold": [0],
    "channel_8": [7],
}


def _router_channel_index(input_channels: dict, port_name: str) -> int:
    """Index of `port_name`'s first channel in the Router's flattened
    output -- i.e. the position `sample[i]` needs in every downstream
    EEG_gpype LSL sample. Mirrors gp.Router's own flattening: ports land in
    dict-iteration order, each contributing len(channels) output channels.
    """
    idx = 0
    for name, channels in input_channels.items():
        if name == port_name:
            return idx
        idx += len(channels)
    raise KeyError(f"{port_name!r} not in input_channels")


THETA_CHANNEL_INDEX = _router_channel_index(ROUTER_INPUT_CHANNELS, "hold")  # channel I want to see


# ============================================================
# Theta closed-loop control
# ============================================================

SONICATION_TIME = 5 #seconds i believe
COOLDOWN_TIME = 15 #sonication time + cooldown time
THETA_THRESHOLD_Z = 1.5    # z-score threshold
MU = 3.12
SIGMA =  5.31
MAD_THRESHOLD = 60 #TESTING       # for artifact rejection in baseline collection
INITIAL_CUTOFF = 50.0   # initial power threshold to exclude extreme artifacts
BUFFER_SIZE = 500
BUFFER_COLLECTION_SIZE = 200 # minimum amount of samples to collect before starting to check for theta threshold crossings
MAX_SONICATIONS = 10   # cap on NUM_SONICATIONS per run
sonication_enabled = False




def listen_for_start():
    global sonication_enabled
    inlet = StreamInlet(resolve_byprop("name", "PsychoPyMarkers")[0])


    while True:
        sample, ts = inlet.pull_sample(timeout=0.1)
        if sample and sample[0] == "START_EXPERIMENT":
            logger.info("Experiment started — enabling LIFU.")
            eeg_trigger_outlet.push_sample(["START_EXPERIMENT_RECEIVED"])
            sonication_enabled = True
            break


def theta_sample_source(stream_name='EEG_gpype', channel_index=THETA_CHANNEL_INDEX, timeout=0.01):
    """Pulls samples from the named LSL stream and yields (theta_val, ts) pairs
    for theta_trigger_loop to consume. This is the only piece of
    theta_trigger_loop that talks to LSL for its input; it's split out so
    theta_trigger_loop's actual decision logic can be fed a different
    (theta_val, ts) source -- e.g. replayed recorded samples in a test --
    without touching the logic itself.
    """
    logger.info("Waiting for theta LSL stream (name=%r)...", stream_name)
    streams = resolve_byprop('name', stream_name, timeout=30)
    if not streams:
        logger.error("No EEG LSL stream found for theta.")
        return


    inlet = StreamInlet(streams[0])
    logger.info("Connected to EEG LSL stream for theta.")


    while RUNNING:
        sample, ts = inlet.pull_sample(timeout=timeout)
        if sample is None:
            continue
        yield sample[channel_index], ts


def theta_trigger_loop(
    sample_source=None,
    *,
    interface=None,
    sonication_time=SONICATION_TIME,
    cooldown_time=COOLDOWN_TIME,
    theta_threshold_z=THETA_THRESHOLD_Z,
    mad_threshold=MAD_THRESHOLD,
    initial_cutoff=INITIAL_CUTOFF,
    buffer_size=BUFFER_SIZE,
    buffer_collection_size=BUFFER_COLLECTION_SIZE,
    max_sonications=MAX_SONICATIONS,
):
    """Applies theta-thresholding + cooldown/artifact-rejection logic to a
    stream of (theta_val, ts) pairs and emits LIFU_ON/OFF markers over LSL.

    sample_source defaults to live LSL data via theta_sample_source(). Pass
    any other iterable of (theta_val, ts) pairs (e.g. replayed recorded
    samples with their original timestamps) to exercise this exact function
    -- unmodified decision logic and marker emission included -- without
    needing a live LSL stream.

    interface defaults to None, which keeps this dry-run: LIFU_ON/OFF markers
    are emitted and sonication_time is simulated with time.sleep(), but no
    hardware is touched. Pass a connected LIFUInterface (see init_hardware(),
    only constructed when HARDWARE_ENABLED) to actually fire the transducer
    via interface.txdevice.start_trigger()/stop_trigger() around the same
    marker emission and cooldown/cap logic.

    The remaining keyword arguments default to the module-level constants of
    the same name (SONICATION_TIME, COOLDOWN_TIME, etc.) but can be
    overridden per-call -- e.g. a test passing a tiny sonication_time/
    cooldown_time and a small max_sonications to exercise the NUM_SONICATIONS
    cap in real time without waiting on production-sized delays.
    """
    NUM_SONICATIONS = 0
    if sample_source is None:
        sample_source = theta_sample_source()


    #theta_history = []
    last_trigger_time = 0
    last_theta_val = None
    logger.info("Starting theta-based closed-loop monitoring...")
    buffer = []


    for theta_val, ts in sample_source:
        if not RUNNING:
            break
        if last_theta_val is not None and theta_val == last_theta_val:
            continue
        last_theta_val = theta_val
        # update rolling buffer
        # not enough data yet → just collect
        if len(buffer) <= buffer_collection_size:
            if theta_val < initial_cutoff:
                buffer.append(theta_val)
                eeg_trigger_outlet.push_sample(["collecting_baseline"])
            continue
        if len(buffer) > buffer_size:
            buffer.pop(0)




        arr = np.array(buffer)
        median = np.median(arr)
        mad = np.median(np.abs(arr - median)) + 1e-6


        z = abs(theta_val - median) / mad


        if z > mad_threshold:
            logger.info(
                f"Artifact detected: {theta_val:.1f} (median={median:.1f}, MAD={mad:.1f}, z={z:.1f})"
            )
            continue  # skip adding this sample to baseline


        # clean sample → keep
        buffer.append(theta_val)

        now = ts
        logger.debug("sonication_enabled=%s", sonication_enabled)

        if (
            sonication_enabled
            and theta_val < mad_threshold
            and theta_val > theta_threshold_z
            and (now - last_trigger_time) > cooldown_time
            and NUM_SONICATIONS < max_sonications
        ):
            logger.info(f"Theta threshold crossed: z={theta_val:.2f}. Triggering LIFU.")
            try:
                eeg_trigger_outlet.push_sample(["LIFU_ON"])
                if interface is not None and not interface.txdevice.start_trigger():
                    logger.error("Failed to start LIFU trigger.")
                    continue
                lifu_num_outlet.push_sample([1.0])
                NUM_SONICATIONS += 1


                time.sleep(sonication_time)

                if interface is not None and not interface.txdevice.stop_trigger():
                    logger.error("Failed to stop LIFU trigger.")
                eeg_trigger_outlet.push_sample(["LIFU_OFF"])
                lifu_num_outlet.push_sample([0.0])


                last_trigger_time = now
                logger.info("Theta-triggered sonication complete.")
            except Exception as e:
                logger.error(f"Error during theta-triggered sonication: {e}")

    return NUM_SONICATIONS


# ============================================================
# g.Pype pipeline
# ============================================================

# gp pipeline for EEG headset


fs = 250


def run_pipeline():
    """
    Runs the g.Pype processing pipeline headlessly (no gpype GUI/scope).
    Real-time visualization of all LSL streams (raw EEG, EEG_gpype, and all
    marker streams) is handled separately by lsl_visualizer.py.


    Unless OW_NO_VISUALIZER is set, lsl_visualizer.py is launched
    automatically as a subprocess and terminated when the pipeline stops.
    """
    p = gp.Pipeline()
    source = gp.BCICore8()

    bandpass = gp.Bandpass(f_lo = 1.0, f_hi = 30.0, order = 4)
    theta_filter = gp.Bandpass(f_lo=4.0, f_hi=7.0, order=4)
    notch60 = gp.Bandstop(f_lo=58, f_hi=62, order=4)


    power = gp.Equation("in**2")
    moving_average = gp.MovingAverage(window_size=50)
    decimator = gp.Decimator(decimation_factor=10)
    hold = gp.Hold()
    theta_z_eq = gp.Equation("(in - 5.36) / 6.60") # MANUALLY CHANGE



    merger = gp.Router(
        input_channels=ROUTER_INPUT_CHANNELS,
        output_channels=[gp.Router.ALL],
    )


    sender = gp.LSLSender(stream_name = "EEG_gpype")  # default name/type; we’ll resolve by type='EEG'


    p.connect(source, notch60)
    p.connect(notch60, bandpass)
    p.connect(bandpass,theta_filter)
    p.connect(theta_filter, power)
    p.connect(power, moving_average)
    p.connect(moving_average, theta_z_eq)
    p.connect(theta_z_eq, decimator)
    p.connect(decimator, hold)


    p.connect(source, merger["channel_1"])
    p.connect(source, merger["channel_2"])
    p.connect(source, merger["channel_3"])
    p.connect(source, merger["channel_4"])
    p.connect(source, merger["channel_5"])
    p.connect(source, merger["channel_6"])
    p.connect(source, merger["channel_7"])
    p.connect(theta_filter, merger["theta_filter"])
    p.connect(power, merger["power"])
    p.connect(moving_average, merger["moving_average"])
    p.connect(hold, merger["hold"])
    p.connect(theta_z_eq, merger["theta_z"])
    p.connect(source, merger["channel_8"])




    p.connect(merger, sender)


    visualizer_proc = None
    if not os.environ.get("OW_NO_VISUALIZER"):
        visualizer_path = Path(__file__).resolve().parent / "lsl_visualizer.py"
        try:
            visualizer_proc = subprocess.Popen(
                [sys.executable, str(visualizer_path)], **_SUBPROCESS_KWARGS
            )
            logger.info("Launched lsl_visualizer.py (pid=%s).", visualizer_proc.pid)
        except OSError as e:
            logger.warning("Could not launch lsl_visualizer.py: %s", e)


    p.start()
    logger.info(
        "g.Pype pipeline running headless (no GUI scope). "
        "lsl_visualizer.py shows all LSL streams (EEG_gpype, markers, etc.) "
        "in real time. Set OW_NO_VISUALIZER=1 to disable auto-launch."
    )
    try:
        while RUNNING:
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted, stopping g.Pype...")
    finally:
        # Each step runs in isolation: p.stop() can block for a while (it
        # waits on gpype's internal threads), and if a second, impatient
        # Ctrl+C lands during that wait it must not skip terminating
        # lsl_visualizer.py -- that's what left the viewer window running
        # before _cleanup_step existed.
        _cleanup_step("stop g.Pype pipeline", p.stop)
        _cleanup_step("terminate lsl_visualizer.py", _terminate_proc, visualizer_proc)


# ============================================================
# Entrypoint
# ============================================================

def main() -> int:
    global RUNNING
    RUNNING = True
    interface = None
    theta_thread = None
    psychopy_proc = None
    lab_recorder_proc = None
    lab_recorder_started = False
    try:
        if HARDWARE_ENABLED and SHAM_RUN:
            logger.info(
                "OW_SHAM_RUN set; skipping init_hardware() -- interface stays None, "
                "so theta_trigger_loop runs its normal dry-run (markers emitted, no "
                "hardware calls) and the LIFU will not sonicate this run."
            )
        elif HARDWARE_ENABLED:
            # Bring up hardware (USB connect, 12V/HV power-on, TX7332 enumeration,
            # beamforming solution) only when actually running this script with
            # OW_HARDWARE_ENABLED set -- importing this module (e.g. for tests)
            # never reaches here.
            try:
                interface, solution = init_hardware()
            except RuntimeError as e:
                logger.error("Hardware init failed: %s", e)
                return 1

        # Start thread to listen for experiment start trigger from PsychoPy
        listen_for_psychopy_thread = threading.Thread(target=listen_for_start, daemon=True)
        listen_for_psychopy_thread.start()


        # Start theta closed-loop thread
        theta_thread = threading.Thread(
            target=theta_trigger_loop, kwargs={"interface": interface}, daemon=False
        )
        theta_thread.start()


        # Start the PsychoPy task now that the marker/EEG plumbing it talks
        # to is already listening.
        psychopy_proc = start_psychopy()


        # Start LabRecorder last, once every other stream/process is already
        # under way. Streams that still aren't online yet (e.g. EEG_gpype,
        # which run_pipeline() below hasn't created, or PsychoPyMarkers,
        # which the task emits once its own window is up) are still folded
        # into the recording automatically as they come online, per its
        # Required Streams config -- see readme.md.
        lab_recorder_proc, lab_recorder_started = start_lab_recorder()


        # Press Run in the Slicer GUI for the user, if that's the hardware
        # path being used (see trigger_slicer_run()'s docstring). Skipped
        # entirely when HARDWARE_ENABLED, since then this script fires the
        # hardware directly instead of relying on Slicer's Run button. Also
        # skipped when SHAM_RUN is set -- Slicer's solution never gets
        # "Run", so it stays unarmed and the LIFU will not sonicate.
        if HARDWARE_ENABLED:
            pass
        elif SHAM_RUN:
            logger.info(
                "OW_SHAM_RUN set; skipping the Slicer auto-run trigger -- Slicer "
                "stays unarmed, so the LIFU will not sonicate this run."
            )
        else:
            trigger_slicer_run()


        # Start g.Pype pipeline
        run_pipeline()


    finally:
            # ALWAYS stop everything when the pipeline stops (including on
            # Ctrl+C): PsychoPy, LabRecorder, LIFU hardware, and the theta
            # thread. The g.Pype pipeline and lsl_visualizer.py are already
            # stopped inside run_pipeline()'s own finally block. Each step
            # below runs via _cleanup_step so one failing/interrupted step
            # (e.g. another Ctrl+C landing mid-join) can't skip the rest.
            RUNNING = False
            _cleanup_step("stop PsychoPy", stop_psychopy, psychopy_proc)
            _cleanup_step("stop LabRecorder", stop_lab_recorder, lab_recorder_proc, lab_recorder_started)
            if interface is not None:
                _cleanup_step("turn off LIFU HV", interface.hvcontroller.turn_hv_off)
            if theta_thread is not None:
                _cleanup_step("join theta thread", theta_thread.join)

    return 0


if __name__ == "__main__":
    sys.exit(main())

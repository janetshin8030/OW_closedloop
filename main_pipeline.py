from __future__ import annotations


import logging
import math
import os
import subprocess
import sys
import threading
import time
import csv
from pathlib import Path


if os.name == 'nt':
    import msvcrt
else:
    import select


import numpy as np
from pylsl import StreamInlet, local_clock, resolve_byprop, StreamInfo, StreamOutlet


import gpype as gp


from openlifu.bf.pulse import Pulse
from openlifu.bf.sequence import Sequence
from openlifu.db import Database
from openlifu.geo import Point
from openlifu.io.LIFUInterface import LIFUInterface
from openlifu.plan.solution import Solution


# name convention
name_and_trial = "demo"

# all CSV output goes here
CSV_DIR = Path("csv_data")
CSV_DIR.mkdir(exist_ok=True)

# logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


# Sending markers to EEG
eeg_trigger_info = StreamInfo('EEG_LIFU_events', 'Markers', 1, 0, 'string')
eeg_trigger_outlet = StreamOutlet(eeg_trigger_info)
logger.info("LIFU to PsychoPy LSL outlet created.")


#sending markers to psychopy
lifu_num_info = StreamInfo('PsychoPy_numeric', 'Markers', 1, 0, 'float32')
lifu_num_outlet = StreamOutlet(lifu_num_info)
logger.info("LIFU to PsychoPy LSL outlet created.")


#global variables for threads
RUNNING = True


#saving markers to csv
def record_lifu_numeric():
    print("Waiting for LIFU_numeric stream...")
    streams = resolve_byprop("name", "EEG_LIFU_events", timeout=30)
    if not streams:
        print("No LIFU_numeric stream found.")
        return


    inlet = StreamInlet(streams[0])
    print("Connected to LIFU_numeric stream.")


    with open(CSV_DIR / f"lifu_markers_1_{name_and_trial}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Time", "marker", "LSL_timestamp"])  # Header


        while RUNNING:
            sample, ts= inlet.pull_sample(timeout=0.1)
            if sample is None:
                continue
            if sample:
                relative_ts = ts - eeg_start_lsl
                writer.writerow([relative_ts, sample[0],ts])
                f.flush()              # <--- forces Python to write
                os.fsync(f.fileno())   # <--- forces OS to write
                print("Wrote marker:", sample[0])




def record_eeg_lsl():
    """
    Record EEG data from LSL to CSV for offline processing.
    This is separate from the g.Pype pipeline's own CSV writing.
    """
    print("Waiting for EEG LSL stream...")
    streams = resolve_byprop('type', 'EEG', timeout=30)
    if not streams:
        print("No EEG LSL stream found.")
        return


    inlet = StreamInlet(streams[0])
    print("Connected to EEG LSL stream.")


    with open(CSV_DIR / f"scope_eeg_{name_and_trial}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        header_written = False


        while RUNNING:
            sample, ts = inlet.pull_sample(timeout=0.01)
            if sample is None:
                continue


            if not header_written:
                header = ["Time"] + [f"Ch{i:02d}" for i in range(1, len(sample)+1)]
                writer.writerow(header)
                header_written = True


            writer.writerow([ts] + sample)
            f.flush()
            os.fsync(f.fileno())
            #print(f"Wrote EEG sample at {ts:.6f}s")




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

SONICATION_TIME = 5 #seconds i believe
COOLDOWN_TIME = 15 #sonication time + cooldown time
THETA_THRESHOLD_Z = 1.5    # z-score threshold
MU = 3.12
SIGMA =  5.31
MAD_THRESHOLD = 60 #TESTING       # for artifact rejection in baseline collection
INITIAL_CUTOFF = 50.0   # initial power threshold to exclude extreme artifacts
BUFFER_SIZE = 500
MAX_SONICATIONS = 10   # cap on NUM_SONICATIONS per run
sonication_enabled = False




def listen_for_start():
    global sonication_enabled
    inlet = StreamInlet(resolve_byprop("name", "PsychoPyMarkers")[0])


    while True:
        sample, ts = inlet.pull_sample(timeout=0.1)
        if sample and sample[0] == "START_EXPERIMENT":
            print("Experiment started — enabling LIFU.")
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
    sonication_time=SONICATION_TIME,
    cooldown_time=COOLDOWN_TIME,
    theta_threshold_z=THETA_THRESHOLD_Z,
    mad_threshold=MAD_THRESHOLD,
    initial_cutoff=INITIAL_CUTOFF,
    buffer_size=BUFFER_SIZE,
    max_sonications=MAX_SONICATIONS,
):
    """Applies theta-thresholding + cooldown/artifact-rejection logic to a
    stream of (theta_val, ts) pairs and emits LIFU_ON/OFF markers over LSL.

    sample_source defaults to live LSL data via theta_sample_source(). Pass
    any other iterable of (theta_val, ts) pairs (e.g. replayed recorded
    samples with their original timestamps) to exercise this exact function
    -- unmodified decision logic and marker emission included -- without
    needing a live LSL stream.

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
        if len(buffer) <= 200:
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
        print(f"sonication_enabled={sonication_enabled}")
       
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
                lifu_num_outlet.push_sample([1.0])
                NUM_SONICATIONS += 1


                time.sleep(sonication_time)
                eeg_trigger_outlet.push_sample(["LIFU_OFF"])
                lifu_num_outlet.push_sample([0.0])


                last_trigger_time = now
                logger.info("Theta-triggered sonication complete.")
            except Exception as e:
                logger.error(f"Error during theta-triggered sonication: {e}")

    return NUM_SONICATIONS


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
    global eeg_start_lsl
    p = gp.Pipeline()
    source = gp.BCICore8()
   
    bandpass = gp.Bandpass(f_lo = 1.0, f_hi = 30.0, order = 4)
    theta_filter = gp.Bandpass(f_lo=4.0, f_hi=7.0, order=4)
    notch60 = gp.Bandstop(f_lo=58, f_hi=62, order=4)


    power = gp.Equation("in**2")
    moving_average = gp.MovingAverage(window_size=50)
    decimator = gp.Decimator(decimation_factor=10)
    hold = gp.Hold()
    theta_z_eq = gp.Equation("(in - 5.36) / 6.60")



    merger = gp.Router(
        input_channels=ROUTER_INPUT_CHANNELS,
        output_channels=[gp.Router.ALL],
    )


    sender = gp.LSLSender(stream_name = "EEG_gpype")  # default name/type; we’ll resolve by type='EEG'
    online_writer = gp.CsvWriter(file_name=str(CSV_DIR / f"thetaEEG_gpype_{name_and_trial}.csv"))
    offline_writer = gp.CsvWriter(file_name=str(CSV_DIR / f"thetaEEG_full_{name_and_trial}.csv"))


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
    p.connect(merger, online_writer)
    p.connect(source, offline_writer)


    visualizer_proc = None
    if not os.environ.get("OW_NO_VISUALIZER"):
        visualizer_path = Path(__file__).resolve().parent / "lsl_visualizer.py"
        try:
            visualizer_proc = subprocess.Popen([sys.executable, str(visualizer_path)])
            logger.info("Launched lsl_visualizer.py (pid=%s).", visualizer_proc.pid)
        except OSError as e:
            logger.warning("Could not launch lsl_visualizer.py: %s", e)


    p.start()
    eeg_start_lsl = local_clock()  # set global start time for LSL relative timestamps NOT SURE IF I NEED THIS
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
        p.stop()
        if visualizer_proc is not None and visualizer_proc.poll() is None:
            visualizer_proc.terminate()
            try:
                visualizer_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                visualizer_proc.kill()


if __name__ == "__main__":
    try:
        # Start thread to listen for experiment start trigger from PsychoPy
        listen_for_psychopy_thread = threading.Thread(target=listen_for_start, daemon=True)
        listen_for_psychopy_thread.start()


        # Start theta closed-loop thread
        theta_thread = threading.Thread(target=theta_trigger_loop, daemon=False)
        theta_thread.start()


        # Start LIFU marker recording thread
        lifu_record_thread = threading.Thread(target=record_lifu_numeric, daemon=False)
        lifu_record_thread.start()


        # Start EEG recording thread
        eeg_record_thread = threading.Thread(target=record_eeg_lsl, daemon=False)
        eeg_record_thread.start()


        # Start g.Pype pipeline
        run_pipeline()


    finally:
            # ALWAYS stop threads when pipeline stops
            RUNNING = False
            theta_thread.join()
            lifu_record_thread.join()

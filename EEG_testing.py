from __future__ import annotations

import logging
import math
import os
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
from hash_func import hash_and_test

import gpype as gp 

from openlifu.bf.pulse import Pulse
from openlifu.bf.sequence import Sequence
from openlifu.db import Database
from openlifu.geo import Point
from openlifu.io.LIFUInterface import LIFUInterface
from openlifu.plan.solution import Solution

# main pipeline from theta detection to LIFU triggering, sends markers to psychopy and EEG files

# logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Prevent duplicate handlers and cluttered terminal output
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

    with open(f"lifu_markers_1_{hash_and_test}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Time", "marker", "LSL_timestamp"])  # Header

        while RUNNING:
            sample, ts= inlet.pull_sample(timeout=1.0)
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

    with open(f"eeg_LSL_gpype{hash_and_test}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        header_written = False

        while RUNNING:
            sample, ts = inlet.pull_sample(timeout=1.0)
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


# beamforming parameters (demo code)
xInput = 0
yInput = 0
zInput = 50

frequency_kHz = 400
voltage = 45.0
duration_msec = 3
interval_msec = 10
num_modules = 1

use_external_power_supply = False
peak_to_peak_voltage = voltage * 2

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
        logger.error("HV NOT fully connected.")
        sys.exit(1)
else:
    logger.info("Using external power supply")

if tx_connected:
    logger.info(f"  TX Connected: {tx_connected}")
    logger.info("LIFU Device fully connected.")
else:
    logger.error("TX NOT fully connected.")
    sys.exit(1)

if not interface.txdevice.ping():
    logger.error("Failed to ping the transmitter device.")
    sys.exit(1)

if not use_external_power_supply and not interface.hvcontroller.ping():
    logger.error("Failed to ping the console device.")
    sys.exit(1)

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


# theta sonication loop (eeg + demo code)

SONICATION_TIME = 5 #seconds i believe  
COOLDOWN_TIME = 7 #sonication time + cooldown time 
THETA_THRESHOLD_Z = 1.5    # z-score threshold
MU = 2.32
SIGMA = 4.18
MAD_THRESHOLD = 60       # for artifact rejection in baseline collection
INITIAL_CUTOFF = 100.0   # initial power threshold to exclude extreme artifacts
BUFFER_SIZE = 500
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

def theta_trigger_loop():
    logger.info("Waiting for theta LSL stream (type='EEG')...")
    streams = resolve_byprop('name', 'EEG_gpype', timeout=30)
    if not streams:
        logger.error("No EEG LSL stream found for theta.")
        return

    inlet = StreamInlet(streams[0])
    logger.info("Connected to EEG LSL stream for theta.")

    #theta_history = []
    last_trigger_time = 0
    last_theta_val = None
    logger.info("Starting theta-based closed-loop monitoring...")
    buffer = []

    while RUNNING:
        sample, ts = inlet.pull_sample(timeout=1.0)
        if sample is None:
            break
        theta_val = sample[5]  # Smoothed Power channel
        if last_theta_val is not None and theta_val == last_theta_val:
            continue
        last_theta_val = theta_val
        # update rolling buffer
        # not enough data yet → just collect
        if len(buffer) <= 200:
            if theta_val < INITIAL_CUTOFF:
                buffer.append(theta_val)
                eeg_trigger_outlet.push_sample(["collecting_baseline"])
            continue
        if len(buffer) > BUFFER_SIZE:
            buffer.pop(0)


        arr = np.array(buffer)
        median = np.median(arr)
        mad = np.median(np.abs(arr - median)) + 1e-6

        z = abs(theta_val - median) / mad

        if z > MAD_THRESHOLD:
            logger.info(
                f"Artifact detected: {theta_val:.1f} (median={median:.1f}, MAD={mad:.1f}, z={z:.1f})"
            )
            continue  # skip adding this sample to baseline

        # clean sample → keep
        buffer.append(theta_val)
        #theta_z =np.abs(theta_val - MU) / SIGMA
        #ts_rel = ts - eeg_start_lsl
        # with open(f"theta_z_values_{hash_and_test}.csv", "a") as f:
        #     f.write(f"{ts_rel},{theta_z}\n")
        
        now = ts
        print(f"sonication_enabled={sonication_enabled}")
        
        if sonication_enabled and theta_val < MAD_THRESHOLD and theta_val > THETA_THRESHOLD_Z and (now - last_trigger_time) > COOLDOWN_TIME:
            logger.info(f"Theta threshold crossed: z={theta_val:.2f}. Triggering LIFU.")
            eeg_trigger_outlet.push_sample(["LIFU_ON"])
            if interface.txdevice.start_trigger():
                logger.info("Trigger Running...") #once ttl works we will take this out
                lifu_num_outlet.push_sample([1.0]) 
                for i in range(int(SONICATION_TIME),0,-1):
                    logger.info(f"Sonication stopping in {i} seconds")
                    time.sleep(1)

                # Wait for threads to finish
                # user_input.join()

                # time.sleep(0.5)  # Give the logging thread time to finish
                if interface.txdevice.stop_trigger():
                    eeg_trigger_outlet.push_sample(["LIFU_OFF"])
                    lifu_num_outlet.push_sample([0.0])
                    last_trigger_time = now
                    logger.info("Theta-triggered sonication complete.")
                else:
                    logger.error("Failed to stop trigger.")
            else:
                logger.error("Failed to get trigger setting.")


# gp pipeline for EEG headset

fs = 250 

def run_pipeline():
    global eeg_start_lsl
    app = gp.MainApp()
    p = gp.Pipeline()
    MU = 2.32
    SIGMA = 4.18
    source = gp.BCICore8()

    theta_filter = gp.Bandpass(f_lo=4.0, f_hi=7.0, order=4)
    notch60 = gp.Bandstop(f_lo=58, f_hi=62, order=4)

    power = gp.Equation("in**2")
    moving_average = gp.MovingAverage(window_size=50)
    decimator = gp.Decimator(decimation_factor=10)
    hold = gp.Hold()
    theta_z_eq = gp.Equation("(in - 2.32) / 4.18")


    merger = gp.Router(
        input_channels={
            "raw_eeg": [0],
            "theta_filter": [0],
            "power": [0],
            "moving_average": [0],
            "theta_z": [0],
            "hold": [0]
        },
        output_channels=[gp.Router.ALL],
    )

    scope = gp.TimeSeriesScope(
        amplitude_limit=20, time_window=5,
        channel_names=[
            "Raw EEG",
            "Theta Filter (4-7Hz)",
            "Instantaneous Power",
            "Smoothed Power",
            "Theta Z-Score",
            "Decimated Power"
        ]
    )

    sender = gp.LSLSender(stream_name = "EEG_gpype")  # default name/type; we’ll resolve by type='EEG'
    online_writer = gp.CsvWriter(file_name=f"thetaEEG_gpype_{hash_and_test}.csv")
    offline_writer = gp.CsvWriter(file_name=f"thetaEEG_full_{hash_and_test}.csv")

    p.connect(source, notch60)
    p.connect(notch60, theta_filter)
    p.connect(theta_filter, power)
    p.connect(power, moving_average)
    p.connect(moving_average, theta_z_eq)
    p.connect(theta_z_eq, decimator)
    p.connect(decimator, hold)


    p.connect(source, merger["raw_eeg"])
    p.connect(theta_filter, merger["theta_filter"])
    p.connect(power, merger["power"])
    p.connect(moving_average, merger["moving_average"])
    p.connect(hold, merger["hold"])
    p.connect(theta_z_eq, merger["theta_z"])


    p.connect(merger, scope)
    p.connect(merger, sender)
    p.connect(merger, online_writer)
    p.connect(source, offline_writer)

    app.add_widget(scope)

    p.start()
    eeg_start_lsl = local_clock()  # set global start time for LSL relative timestamps
    try:
        app.run()          # blocks until GUI close or Ctrl+C
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted, stopping g.Pype...")
    finally:
        p.stop()  

    # p.start()

    # app.run()

    # p.stop()

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

            try:
                interface.hvcontroller.turn_hv_off()
            except:
                pass

            theta_thread.join()
            lifu_record_thread.join()
from __future__ import annotations

import logging
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

import gpype as gp 

from openlifu.bf.pulse import Pulse
from openlifu.bf.sequence import Sequence
from openlifu.db import Database
from openlifu.geo import Point
from openlifu.io.LIFUInterface import LIFUInterface
from openlifu.plan.solution import Solution

# -------------------------------------------------------
# Logging
# -------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False

# -------------------------------------------------------
# LIFU → PsychoPy stream
# -------------------------------------------------------
lifu_info = StreamInfo('LIFUEvents', 'Markers', 1, 0, 'string')
lifu_outlet = StreamOutlet(lifu_info)
logger.info("LIFU → PsychoPy LSL outlet created.")

lifu_num_info = StreamInfo('LIFU_numeric', 'Markers', 1, 0, 'float32')
lifu_num_outlet = StreamOutlet(lifu_num_info)

def record_lifu_numeric():
    print("Waiting for LIFU_numeric stream...")
    streams = resolve_byprop("name", "LIFU_numeric", timeout=30)
    if not streams:
        print("No LIFU_numeric stream found.")
        return

    inlet = StreamInlet(streams[0])
    print("Connected to LIFU_numeric stream.")

    with open("lifu_markers.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Time", "marker"])

        while True:
            sample, ts= inlet.pull_sample(timeout=1.0)
            if sample:
                relative_ts = ts - eeg_start_lsl
                writer.writerow([relative_ts, sample[0]])
                f.flush()              # <--- forces Python to write
                os.fsync(f.fileno())   # <--- forces OS to write
                print("Wrote marker:", sample[0])


# -------------------------------------------------------
# Beamforming parameters
# -------------------------------------------------------
xInput = -10
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

if not use_external_power_supply and not tx_connected:
    logger.warning("TX device not connected. Attempting to turn on 12V...")
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


# -------------------------------------------------------
# Theta-based closed-loop logic (using LSL theta stream)
# -------------------------------------------------------

SONICATION_TIME = 5
COOLDOWN_TIME = 10
THETA_THRESHOLD_Z = 1.5
SMOOTHING_WINDOW = 5          # samples of decimated theta
MU = 5.0
SIGMA = 5.0       # number of decimated samples for baseline

def theta_trigger_loop():
    logger.info("Waiting for theta LSL stream (type='EEG')...")
    streams = resolve_byprop('type', 'EEG', timeout=30)
    if not streams:
        logger.error("No EEG LSL stream found for theta.")
        return

    inlet = StreamInlet(streams[0])
    logger.info("Connected to EEG LSL stream for theta.")

    theta_history = []
    last_trigger_time = 0
    logger.info("Starting theta-based closed-loop monitoring...")

    while True:
        sample, ts = inlet.pull_sample(timeout=1.0)
        if sample is None:
            continue

        theta_val = sample[4]
        theta_z = (theta_val - MU) / SIGMA

        theta_history.append(theta_z)
        if len(theta_history) > SMOOTHING_WINDOW:
            theta_history.pop(0)

        smoothed_theta = np.mean(theta_history)
        now = time.time()

        if smoothed_theta > THETA_THRESHOLD_Z and (now - last_trigger_time) > COOLDOWN_TIME:
            logger.info(f"Theta threshold crossed: z={smoothed_theta:.2f}. Triggering LIFU.")
            try:
                interface.hvcontroller.turn_hv_on()
                time.sleep(0.3)

                lifu_outlet.push_sample(["THETA_TRIGGER"])
                lifu_outlet.push_sample(["LIFU_ON"])
                lifu_num_outlet.push_sample([1.0]) 
                interface.start_sonication()
                time.sleep(SONICATION_TIME)
                interface.stop_sonication()
                lifu_outlet.push_sample(["LIFU_OFF"])
                lifu_num_outlet.push_sample([0.0]) 

                interface.hvcontroller.turn_hv_off()
                last_trigger_time = time.time()
                logger.info("Theta-triggered sonication complete.")
            except Exception as e:
                logger.error(f"Error during theta-triggered sonication: {e}")

# -------------------------------------------------------
# gp pipeline for theta computation + LSL sender
# -------------------------------------------------------

hash_value = 0 #set simple unique id
fs = 250  # set to your actual sampling rate

def run_pipeline():
    app = gp.MainApp()
    p = gp.Pipeline()

    source = gp.BCICore8()

    theta_filter = gp.Bandpass(f_lo=4.0, f_hi=7.0, order=4)
    notch60 = gp.Bandstop(f_lo=58, f_hi=62, order=4)

    power = gp.Equation("in**2")
    moving_average = gp.MovingAverage(window_size=125)
    decimator = gp.Decimator(decimation_factor=25)
    hold = gp.Hold()

    merger = gp.Router(
        input_channels={
            "raw_eeg": [0],
            "theta_filter": [0],
            "power": [0],
            "moving_average": [0],
            "hold": [0],
        },
        output_channels=[gp.Router.ALL],
    )

    scope = gp.TimeSeriesScope(
        amplitude_limit=20, time_window=10,
        channel_names=[
            "Raw EEG",
            "Theta Filter (4-7Hz)",
            "Instantaneous Power",
            "Smoothed Power",
            "Decimated Trigger Value"
        ]
    )

    sender = gp.LSLSender()
    writer = gp.CsvWriter(file_name=f"thetaPSD_{hash_value}.csv")


    p.connect(source, notch60)
    p.connect(notch60, theta_filter)
    p.connect(theta_filter, power)
    p.connect(power, moving_average)
    p.connect(moving_average, decimator)
    p.connect(decimator, hold)

    p.connect(source, merger["raw_eeg"])
    p.connect(theta_filter, merger["theta_filter"])
    p.connect(power, merger["power"])
    p.connect(moving_average, merger["moving_average"])
    p.connect(hold, merger["hold"])


    p.connect(merger, scope)
    p.connect(merger, sender)
    p.connect(merger, writer)

    app.add_widget(scope)

    p.start()

    app.run()

    p.stop()

if __name__ == "__main__":
    try:
        # Start theta closed-loop thread
        theta_thread = threading.Thread(target=theta_trigger_loop, daemon=True)
        theta_thread.start()

        # Start LIFU marker recording thread
        lifu_record_thread = threading.Thread(target=record_lifu_numeric, daemon=True)
        lifu_record_thread.start()

        # Start gp.Pype pipeline
        eeg_start_lsl = local_clock()
        run_pipeline()

    except KeyboardInterrupt:
        logger.info("Interrupted by user, turning HV off and exiting...")
        try:
            interface.hvcontroller.turn_hv_off()
        except Exception:
            pass
        sys.exit(0)


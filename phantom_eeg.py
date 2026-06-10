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

# DIRECTLY from gpype documentation -- just added LIFU sonication

fs = 250  # Sampling frequency in Hz

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False

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
rapid_temp_increase_per_second_shutoff_C = 5

console_shutoff_temp_C = 70.0 # Console shutoff temperature in Celsius
tx_shutoff_temp_C = 70.0 # TX device shutoff temperature in Celsius
ambient_shutoff_temp_C = 70.0 # Ambient shutoff temperature in Celsius

peak_to_peak_voltage = voltage * 2

db_path = Path(r"C:\Users\jshin\Downloads\OpenLIFU-python\OpenLIFU-python\db_dvc")
db = Database(db_path)
arr = db.load_transducer(f"openlifu_{num_modules}x400_evt1")
arr.sort_by_pin()

target = Point(position=(xInput, yInput, zInput), units="mm")
target = Point(position=(xInput,yInput,zInput), units="mm")
focus = target.get_position(units="mm")
distances = np.sqrt(np.sum((focus - arr.get_positions(units="mm"))**2, 1)).reshape(1,-1)
tof = distances*1e-3 / 1500
delays = tof.max() - tof
#delays = delays*0.0


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

stop_logging = False

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

profile_index = 1
profile_increment = True
trigger_mode = "continuous"
log_interval = 1

interface.set_solution(
    solution=solution,
    profile_index=1,
    profile_increment=False,
    trigger_mode="continuous"
)

logger.info("Get Trigger")
trigger_setting = interface.txdevice.get_trigger_json()
if trigger_setting:
    logger.info(f"Trigger Setting: {trigger_setting}")
else:
    logger.error("Failed to get trigger setting.")
    sys.exit(1)

duty_cycle = int((duration_msec/interval_msec) * 100)
if duty_cycle > 50:
    logger.warning("❗❗ Duty cycle is above 50% ❗❗")

logger.info(f"User parameters set: \n\
    Module Invert: {arr.module_invert}\n\
    Frequency: {frequency_kHz}kHz\n\
    Voltage Per Rail: {voltage}V\n\
    Voltage Peak to Peak: {peak_to_peak_voltage}V\n\
    Duration: {duration_msec}ms\n\
    Interval: {interval_msec}ms\n\
    Duty Cycle: {duty_cycle}%\n\
    Use External Power Supply: {use_external_power_supply}\n\
    General Temp Safety Shutoff: Increase of {rapid_temp_increase_per_second_shutoff_C}°C within {log_interval}s at any point.\n")

def turn_off_console_and_tx():
    if not use_external_power_supply:
        logger.info("Attempting to turn off High Voltage...")
        interface.hvcontroller.turn_hv_off()
        if interface.hvcontroller.get_hv_status():
            logger.error("High Voltage is still on.")
        else:
            logger.info("High Voltage successfully turned off.")


        logger.info("Attempting to turn off 12V...")
        interface.hvcontroller.turn_12v_off()
        if interface.hvcontroller.get_12v_status():
            logger.error("12V is still on.")
        else:
            logger.info("12V successfully turned off.")


shutdown_event = threading.Event()


#SONICATION THROUGH LSL
def marker_sonication_trigger():
    logger.info("Waiting for theta LSL stream (type='EEG')...")
    streams = resolve_byprop('name', 'keyboard_markers', timeout=30)
    if not streams:
        logger.error("No EEG LSL stream found for theta.")
        return

    inlet = StreamInlet(streams[0])
    logger.info("Connected to EEG LSL stream for theta.")

    last_trigger_time = 0
    COOLDOWN_WINDOW = 10.0 # greater than sonication time
    SONICATION_TIME = 10.0


    while True:
        sample, ts = inlet.pull_sample(timeout=1.0)
        if sample is None:
            continue
        value = sample[8]  # the channel for markers
        current_time = ts
        if value == 0:
            continue
        if value == 38 and current_time - last_trigger_time > COOLDOWN_WINDOW:  
            if interface.txdevice.start_trigger():
                logger.info("Trigger Running...")

                for i in range(int(SONICATION_TIME),0,-1):
                    logger.info(f"Sonication stopping in {i} seconds")
                    time.sleep(1)

                # Wait for threads to finish
                # user_input.join()

                # time.sleep(0.5)  # Give the logging thread time to finish
                if interface.txdevice.stop_trigger():
                    logger.info("Trigger stopped successfully.")
                    last_trigger_time = ts
                else:
                    logger.error("Failed to stop trigger.")
            else:
                logger.error("Failed to get trigger setting.")
                            # try:
                #     logger.info(f"Triggering sonication at theta=1 (value={value})")
                #     interface.hvcontroller.turn_hv_on()
                #     time.sleep(0.3)
                #     interface.start_sonication()
                #     last_trigger_time = current_time
                #     time.sleep(SONICATION_TIME)
                #     interface.stop_sonication()
                #     interface.hvcontroller.turn_hv_off()
                #     logger.info("Theta-triggered sonication complete.")
                # except Exception as e:
                #     logger.error(f"Error during theta-triggered sonication: {e}")






if __name__ == "__main__":
    app = gp.MainApp()

    # Create real-time processing pipeline for EEG data
    p = gp.Pipeline()
    source = gp.BCICore8()

    # === SIGNAL CONDITIONING STAGE ===
    # Bandpass filter: Extract standard EEG frequency range
    # 1-30 Hz preserves all major brain rhythms while removing:
    # - DC drift and movement artifacts (<1 Hz)
    # - EMG muscle artifacts and high-frequency noise (>30 Hz)
    bandpass = gp.Bandpass(
        f_lo=1, f_hi=30  # High-pass: remove DC and slow drift
    )  # Low-pass: remove muscle artifacts

    # === POWER LINE INTERFERENCE REMOVAL ===
    # Notch filter for 50 Hz power line noise (European standard)
    # 48-52 Hz range accounts for slight frequency variations
    notch50 = gp.Bandstop(
        f_lo=48, f_hi=52  # Lower bound of 50 Hz notch
    )  # Upper bound of 50 Hz notch

    # Notch filter for 60 Hz power line noise (American standard)
    # 58-62 Hz range accounts for slight frequency variations
    # Both filters ensure compatibility with different power systems
    notch60 = gp.Bandstop(
        f_lo=58, f_hi=62  # Lower bound of 60 Hz notch
    )  # Upper bound of 60 Hz notch

    keyboard = gp.Keyboard()
    router = gp.Router(input_channels= [gp.Router.ALL, gp.Router.ALL])
    mk = gp.TimeSeriesScope.Markers
    markers = [ mk(color="r", label="up", channel=8, value=38)]
    csv_markers =  gp.CsvWriter(file_name=f"marker.csv")
    sender = gp.LSLSender(stream_name = "keyboard_markers")

    # === REAL-TIME VISUALIZATION ===
    # Professional EEG scope with clinical amplitude scaling
    # 50 µV range covers typical EEG signal amplitudes
    # 10-second window provides good temporal context
    scope = gp.TimeSeriesScope(
        amplitude_limit=50, time_window=10, markers = markers  # ±50 µV range
    )  # 10-second display

    # === PIPELINE CONNECTIONS ===
    # Create signal processing chain: Hardware → Filtering → Visualization
    # Order matters: bandpass first, then notch filters, finally display

    # Connect hardware source to initial bandpass filter
    p.connect(source, bandpass)

    # Connect bandpass output to first notch filter (50 Hz)
    p.connect(bandpass, notch50)

    # Connect first notch to second notch filter (60 Hz)
    p.connect(notch50, notch60)

    # Connect final filtered signal to visualization scope
    p.connect(notch60, router['in1'])
    p.connect(keyboard, router['in2'])
    p.connect(router, scope)

    p.connect(router, csv_markers)  # Log keyboard events to CSV file
    p.connect(router, sender)

    # === APPLICATION SETUP ===
    # Add visualization widget to main application window
    app.add_widget(scope)

    # === EXECUTION ===
    trigger_thread = threading.Thread(
        target=marker_sonication_trigger,
        daemon=True,
        )
    trigger_thread.start()
    # Start real-time data acquisition and processing
    p.start()  # Initialize hardware and begin data flow
    app.run()  # Start GUI event loop (blocks until window closes)
    p.stop()  # Clean shutdown: stop hardware and close connections
    turn_off_console_and_tx()
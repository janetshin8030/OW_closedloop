from __future__ import annotations

import logging
import os
import sys
import threading
import time
from pathlib import Path

if os.name == 'nt':
    import msvcrt
else:
    import select

import numpy as np
from pylsl import StreamInlet, resolve_byprop

from openlifu.bf.pulse import Pulse
from openlifu.bf.sequence import Sequence
from openlifu.db import Database
from openlifu.geo import Point
from openlifu.io.LIFUInterface import LIFUInterface
from openlifu.plan.solution import Solution
from pylsl import StreamInfo, StreamOutlet

# ---- LIFU → PsychoPy stream ----
lifu_info = StreamInfo('LIFUEvents', 'Markers', 1, 0, 'string')
lifu_outlet = StreamOutlet(lifu_info)
print("LIFU → PsychoPy LSL outlet created.")


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

log_interval = 1

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
distances = np.sqrt(np.sum((focus - positions)**2, axis=1)).reshape(1, -1)

speed_of_sound = 1500
tof = distances * 1e-3 / speed_of_sound
delays = tof.max() - tof

apodizations = np.ones((1, arr.numelements()))

#----------------------------------------------- 
# Setting up LIFU Device
#-----------------------------------------------

logger.info("Starting LIFU Test Script...")
interface = LIFUInterface(ext_power_supply=use_external_power_supply)
tx_connected, hv_connected = interface.is_device_connected()

if not use_external_power_supply and not tx_connected:
    logger.warning("TX device not connected. Attempting to turn on 12V...")
    interface.hvcontroller.turn_12v_on()

    # Give time for the TX device to power up and enumerate over USB
    time.sleep(2)

    # Cleanup and recreate interface to reinitialize USB devices
    interface.stop_monitoring()
    del interface
    time.sleep(1)  # Short delay before recreating

    logger.info("Reinitializing LIFU interface after powering 12V...")
    interface =  LIFUInterface(ext_power_supply=use_external_power_supply)

    # Re-check connection
    tx_connected, hv_connected = interface.is_device_connected()

if not use_external_power_supply:
    if hv_connected:
        logger.info(f"  HV Connected: {hv_connected}")
    else:
        logger.error("❌ HV NOT fully connected.")
        sys.exit(1)
else:
    logger.info("  Using external power supply")

if tx_connected:
    logger.info(f"  TX Connected: {tx_connected}")
    logger.info("✅ LIFU Device fully connected.")
else:
    logger.error("❌ TX NOT fully connected.")
    sys.exit(1)

stop_logging = False  # flag to signal the logging thread to stop

# Verify communication with the devices
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
elif num_tx_devices == num_modules*2:
    logger.info(f"Number of TX7332 devices found: {num_tx_devices}")
    numelements = 32*num_tx_devices
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
# Connect to PsychoPy LSL stream
# -------------------------------------------------------
logger.info("Waiting for PsychoPy marker stream...")
streams = resolve_byprop('name', 'PsychoPyMarkers', timeout=30)
if not streams:
    logger.error("No PsychoPy marker stream found.")
    sys.exit(1)

inlet = StreamInlet(streams[0])
logger.info("Connected to PsychoPy marker stream.")

# -------------------------------------------------------
# SONICATION LOGIC WITH PYLSL
# -------------------------------------------------------
SONICATION_TIME = 5
COOLDOWN_TIME = 10
last_sonication_time = 0

logger.info("Listening for INCORRECT markers...")

try:
    while True:
        sample, timestamp = inlet.pull_sample(timeout=0.1)
        if sample is None:
            continue

        marker = sample[0]
        logger.info(f"Received marker: {marker}")

        if marker == "INCORRECT":
            now = time.time()

            if now - last_sonication_time < COOLDOWN_TIME:
                logger.info("Cooldown active. Ignoring INCORRECT.")
                continue

            logger.info("Starting 5-second sonication due to incorrect trial...")

            interface.hvcontroller.turn_hv_on()
            time.sleep(0.3)

            lifu_outlet.push_sample(["LIFU_ON"])
            interface.start_sonication()
            time.sleep(SONICATION_TIME)
            interface.stop_sonication()
            lifu_outlet.push_sample(["LIFU_OFF"])

            interface.hvcontroller.turn_hv_off()

            last_sonication_time = time.time()
            logger.info("Sonication complete.")

except KeyboardInterrupt:
    logger.info("Interrupted by user, turning HV off and exiting...")
    try:
        interface.hvcontroller.turn_hv_off()
    except Exception:
        pass

    sys.exit(0)
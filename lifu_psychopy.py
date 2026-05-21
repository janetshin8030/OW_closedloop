import time
import logging
import numpy as np
from pathlib import Path
from pylsl import StreamInlet, resolve_byprop

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
# Beamforming parameters (same as your original script)
# -------------------------------------------------------
xInput, yInput, zInput = -10, 0, 50
frequency_kHz = 400
voltage = 45.0
duration_msec = 3
interval_msec = 10
num_modules = 1

# -------------------------------------------------------
# Load transducer geometry
# -------------------------------------------------------
here = Path(__file__).parent.resolve()
db_path = here / ".." / "db_dvc"
db = Database(db_path)
arr = db.load_transducer(f"openlifu_{num_modules}x400_evt1")
arr.sort_by_pin()

# -------------------------------------------------------
# Compute delays for the SAME FOCUS
# -------------------------------------------------------
target = Point(position=(xInput, yInput, zInput), units="mm")
focus = target.get_position(units="mm")

positions = arr.get_positions(units="mm")
distances = np.sqrt(np.sum((focus - positions)**2, axis=1)).reshape(1, -1)

speed_of_sound = 1500
tof = distances * 1e-3 / speed_of_sound
delays = tof.max() - tof

apodizations = np.ones((1, arr.numelements()))

# -------------------------------------------------------
# Build pulse + sequence
# -------------------------------------------------------
pulse = Pulse(
    frequency=frequency_kHz * 1e3,
    duration=duration_msec * 1e-3
)

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

# -------------------------------------------------------
# Connect to LIFU hardware
# -------------------------------------------------------
logger.info("Connecting to LIFU...")
interface = LIFUInterface(ext_power_supply=False)

tx_connected, hv_connected = interface.is_device_connected()
if not tx_connected or not hv_connected:
    raise RuntimeError("LIFU hardware not fully connected.")

logger.info("Connected.")

interface.set_solution(
    solution=solution,
    profile_index=1,
    profile_increment=False,
    trigger_mode="continuous"
)

# -------------------------------------------------------
# Connect to PsychoPy LSL stream
# -------------------------------------------------------
logger.info("Waiting for PsychoPy marker stream...")
streams = resolve_byprop('name', 'PsychoPyMarkers', timeout=30)
if not streams:
    raise RuntimeError("No PsychoPy marker stream found.")

inlet = StreamInlet(streams[0])
logger.info("Connected to PsychoPy marker stream.")

# -------------------------------------------------------
# Closed-loop sonication logic
# -------------------------------------------------------
SONICATION_TIME = 5      # seconds
COOLDOWN_TIME = 10       # seconds between sonications
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

            interface.start_sonication()
            time.sleep(SONICATION_TIME)
            interface.stop_sonication()

            interface.hvcontroller.turn_hv_off()

            last_sonication_time = time.time()
            logger.info("Sonication complete.")

except KeyboardInterrupt:
    logger.info("Interrupted by user, turning HV off and exiting...")
    try:
        interface.hvcontroller.turn_hv_off()
    except Exception:
        pass

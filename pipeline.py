from __future__ import annotations

import sys
import time
import threading
import logging

import numpy as np
from scipy.signal import welch
from pylsl import StreamInlet, resolve_byprop, StreamOutlet, StreamInfo
from collections import deque

from openlifu.io.LIFUInterface import LIFUInterface


# LOGGING
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
# LSL MARKER STREAM FOR LIFU EVENTS
marker_info = StreamInfo('LIFU_Markers', 'Markers', 1, 0, 'string', 'lifu_marker_stream')
marker_outlet = StreamOutlet(marker_info)


# LIFU CONNECTION (USING GUI PROFILE)
def connect_lifu(ext_power_supply: bool = False, profile_index: int = 1):
    logger.info("Connecting to LIFU console...")
    interface = LIFUInterface(ext_power_supply=ext_power_supply)
    tx_connected, hv_connected = interface.is_device_connected()

    if not tx_connected or (not ext_power_supply and not hv_connected):
        logger.error(f"LIFU hardware not fully connected. TX={tx_connected}, HV={hv_connected}")
        sys.exit(1)

    logger.info("LIFU connected.")
    logger.info(f"Selecting profile {profile_index} configured via OpenLIFU GUI...")

    # Activate profile on TX device
    interface.txdevice.set_active_profile(profile_index)

    trigger_mode = "continuous"
    profile_increment = False

    # We pass solution=None because the profile is already stored in the console
    interface.set_solution(
        solution=None,
        profile_index=profile_index,
        profile_increment=profile_increment,
        trigger_mode=trigger_mode
    )

    logger.info("Profile loaded successfully from console.")
    return interface


# THETA CALCULATION
FS = 250          # EEG sampling rate (Hz)
WINDOW_SEC = 1.0  # window length in seconds
WINDOW_SAMPLES = int(FS * WINDOW_SEC)
THETA_BAND = (4, 7)
mu = 5.0 #INSERT
sigma = 1.2 #INSERT

def compute_theta_power(samples: np.ndarray, fs: int = FS) -> float:
    freqs, psd = welch(samples, fs=fs, nperseg=WINDOW_SAMPLES)
    mask = (freqs >= THETA_BAND[0]) & (freqs <= THETA_BAND[1])
    return float(np.mean(psd[mask]))


def get_theta_state(
    inlet: StreamInlet,
    mu: float,
    sigma: float,
    channels: list[int],
    threshold: float = 1.5,
    sustain: int = 3,
    step_size: int = 25  # 100 ms step at 250 Hz
) -> int:

    # Initialize static variables
    if not hasattr(get_theta_state, "buf"):
        get_theta_state.buf = deque(maxlen=WINDOW_SAMPLES)
        get_theta_state.counter = 0
        get_theta_state.sample_counter = 0

    # Pull one sample
    sample, _ = inlet.pull_sample(timeout=0.0)
    if sample is None:
        return 0

    # Add selected channels to buffer
    get_theta_state.buf.append([sample[ch] for ch in channels])
    get_theta_state.sample_counter += 1

    # Not enough data yet
    if len(get_theta_state.buf) < WINDOW_SAMPLES:
        return 0

    # Only compute theta every "step_size" samples
    if get_theta_state.sample_counter < step_size:
        return 0
    get_theta_state.sample_counter = 0

    # Convert buffer to array
    window = np.array(get_theta_state.buf)

    # Compute theta power across channels
    theta = np.mean([
        compute_theta_power(window[:, i])
        for i in range(len(channels))
    ])

    # Z-score
    z = (theta - mu) / sigma

    # Sustained threshold logic
    if z > threshold:
        get_theta_state.counter += 1
    else:
        get_theta_state.counter = 0

    return 1 if get_theta_state.counter >= sustain else 0


# MAIN CLOSED-LOOP CONTROLLER
def main():
    # 1) Connect to LIFU (profile configured via OpenLIFU GUI)
    PROFILE_INDEX = 1
    interface = connect_lifu(ext_power_supply=False, profile_index=PROFILE_INDEX)

    # 2) Connect to EEG LSL stream
    print("Resolving EEG stream...")
    streams = resolve_byprop('name', 'PsychoPyMarkers', timeout=10)
    if not streams:
        print("No EEG LSL stream found. Is the Unicorn LSL Streamer running?")
        sys.exit(1)
    eeg_inlet = StreamInlet(streams[0])
    print("EEG stream found.")

    # 3) Baseline calibration
    # Choose channels appropriate for your montage (e.g., 0,1,2 = Fz, C3, Cz)
    CHANNELS = [0, 1, 2]
    # mu, sigma = mu,sigma --> already defined globally

    # 4) Closed-loop parameters
    COOLDOWN = 45            # seconds between sonications
    SONICATION_DURATION = 15 # seconds of LIFU per trigger
    last_sonication_time = 0
    is_sonicating = False

    def run_sonication():
        nonlocal is_sonicating, last_sonication_time

        # Send LIFU_START marker
        marker_outlet.push_sample(["LIFU_START"])
        logger.info("Marker sent: LIFU_START")

        if interface.start_sonication():
            logger.info("Sonication running...")
            time.sleep(SONICATION_DURATION)
            interface.stop_sonication()
            logger.info("Sonication complete. Cooldown active.")
            # Send LIFU_STOP marker
            marker_outlet.push_sample(["LIFU_STOP"])
            logger.info("Marker sent: LIFU_STOP")
        else:
            logger.error("Failed to start sonication.")
        is_sonicating = False

    try:
        print("Closed-loop LIFU running... Press Ctrl+C to stop.")
        while True:
            theta_state = get_theta_state(
                eeg_inlet,
                mu=mu,
                sigma=sigma,
                channels=CHANNELS,
                threshold=1.5 *sigma,
                sustain=3
            )

            now = time.time()

            if theta_state == 1 and not is_sonicating and (now - last_sonication_time) > COOLDOWN:
                print("Theta threshold exceeded → TRIGGERING LIFU")
                last_sonication_time = now
                is_sonicating = True
                threading.Thread(target=run_sonication, daemon=True).start()
            else:
                print(f"ThetaState={theta_state}")

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("Stopping closed-loop...")
        try:
            interface.hvcontroller.turn_hv_off()
            interface.hvcontroller.turn_12v_off()
        except Exception as e:
            logger.error(f"Error turning off HV/12V: {e}")
            interface.stop_sonication()
            interface.hvcontroller.turn_hv_off()
            interface.hvcontroller.turn_12v_off()


if __name__ == "__main__":
    main()

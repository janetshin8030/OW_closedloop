from __future__ import annotations
import time, logging, threading
import sys
import pandas as pd
from pylsl import StreamInlet, resolve_byprop
from openlifu.io.LIFUInterface import LIFUInterface

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)

def connect_lifu(profile_index=1):
    interface = LIFUInterface(ext_power_supply=False)
    tx, hv = interface.is_device_connected()
    if not tx:
        raise RuntimeError('TX not connected')
    if not hv:
        raise RuntimeError('HV controller not connected')
    interface.txdevice.set_active_profile(profile_index)
    interface.set_solution(solution=None,
                           profile_index=profile_index,
                           profile_increment=False,
                           trigger_mode='continuous')
    return interface

def main():
    PROFILE = 1
    SONICATION_DURATION = 5   # seconds
    COOLDOWN = 20             # seconds

    interface = connect_lifu(PROFILE)
    interface.hvcontroller.turn_hv_on()
    time.sleep(0.5)

    print('Waiting for PsychoPy marker stream...')

    # Look specifically for the stream named "PsychoPyMarkers"
    streams = resolve_byprop('name', 'PsychoPyMarkers', timeout=10)

    if not streams:
        print("No PsychoPy marker stream found. Is PsychoPy running?")
        sys.exit(1)

    # Connect to the first matching stream
    inlet = StreamInlet(streams[0])
    print("Connected to PsychoPy marker stream.")

    last_sonication = 0
    is_sonicating = False

    def run_sonication():
        nonlocal is_sonicating, last_sonication
        is_sonicating = True
        last_sonication = time.time()
        logger.info('Starting sonication...')
        interface.start_trigger()
        time.sleep(SONICATION_DURATION)
        interface.stop_trigger()
        logger.info('Sonication complete.')
        is_sonicating = False

    try:
        print('Listening for INCORRECT markers...')
        while True:
            marker, _ = inlet.pull_sample(timeout=0.1)
            if marker:
                event = marker[0]
                print(f'Received marker: {event}')
                if event == 'INCORRECT':
                    now = time.time()
                    if not is_sonicating and (now - last_sonication) > COOLDOWN:
                        threading.Thread(target=run_sonication, daemon=True).start()
                    else:
                        print('Cooldown active — ignoring trigger.')
            time.sleep(0.01)
    except KeyboardInterrupt:
        print('Stopping listener...')
    finally:
        try:
            interface.stop_trigger()
        except Exception:
            pass
        interface.hvcontroller.turn_hv_off()

if __name__ == '__main__':
    main()

from pylsl import StreamInlet, resolve_byprop
import numpy as np
import logging
import time
import threading
import sys
import gpype as gp

# main issue is that if in the beginning it makes the MAD too small, it will never adjust properly
hash_and_test = "stroop_test"
DURATION = 100  # seconds
BUFFER_SIZE = 500
MAD_THRESHOLD = 6
INITIAL_CUTOFF = 100.0  # initial power threshold to exclude extreme artifacts during early collection

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


def run_pipeline():
    app = gp.MainApp()
    p = gp.Pipeline()

    source = gp.BCICore8()

    theta_filter = gp.Bandpass(f_lo=4.0, f_hi=7.0, order=4)
    notch60 = gp.Bandstop(f_lo=58, f_hi=62, order=4)

    power = gp.Equation("in**2")
    moving_average = gp.MovingAverage(window_size=50)

    merger = gp.Router(
        input_channels={
            "raw_eeg": [0],
            "theta_filter": [0],
            "power": [0],
            "moving_average": [0],
        },
        output_channels=[gp.Router.ALL],
    )

    scope = gp.TimeSeriesScope(
        amplitude_limit=20,
        time_window=10,
        channel_names=[
            "Raw EEG",
            "Theta Filter (4-7Hz)",
            "Instantaneous Power",
            "Smoothed Power",
        ],
    )

    sender = gp.LSLSender()  # default name/type; we’ll resolve by type='EEG'

    p.connect(source, notch60)
    p.connect(notch60, theta_filter)
    p.connect(theta_filter, power)
    p.connect(power, moving_average)

    p.connect(source, merger["raw_eeg"])
    p.connect(theta_filter, merger["theta_filter"])
    p.connect(power, merger["power"])
    p.connect(moving_average, merger["moving_average"])

    p.connect(merger, sender)
    p.connect(merger, scope)

    app.add_widget(scope)

    p.start()
    app.run()
    p.stop()


def theta_calibration():
    logger.info("Waiting for theta LSL stream (type='EEG')...")
    streams = resolve_byprop('type', 'EEG', timeout=30)
    if not streams:
        logger.error("No EEG LSL stream found for theta.")
        return []

    inlet = StreamInlet(streams[0])
    logger.info(f"Connected to EEG LSL stream: {streams[0].name()}")

    buffer = []
    theta_history = []
    start_time = time.time()
    logger.info("Starting theta-based baseline collection...")

    while time.time() - start_time < DURATION:
        sample, ts = inlet.pull_sample(timeout=1.0)
        if sample is None:
            continue

        theta_val = sample[3]  # Smoothed Power channel
        # update rolling buffer
        # not enough data yet → just collect
        if len(buffer) < 50:
            if theta_val < INITIAL_CUTOFF:
                theta_history.append(theta_val)
                buffer.append(theta_val)
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
        theta_history.append(theta_val)
        buffer.append(theta_val)

    return theta_history


if __name__ == "__main__":
    try:
        # Qt should NOT run in a daemon thread
        pipeline_thread = threading.Thread(target=run_pipeline)
        pipeline_thread.start()

        time.sleep(2)  # allow LSL stream to appear

        theta_values = theta_calibration()
        print("Collected samples:", len(theta_values))
        print("min=", np.min(theta_values), "max=", np.max(theta_values))

        if len(theta_values) == 0:
            print("No clean samples collected; relax MAD_THRESHOLD or check channel index.")
        else:
            mu = np.mean(theta_values) # mean or median???
            sigma = np.std(theta_values)
            print("\n=== Baseline Complete ===")
            print(f"Mean: {mu:.2f}, Std Dev: {sigma:.2f}")

        # wait for you to close the gpype window
        pipeline_thread.join()

    except KeyboardInterrupt:
        logger.info("Interrupted by user, exiting...")
        sys.exit(0)

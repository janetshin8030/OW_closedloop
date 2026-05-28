
from pylsl import StreamInlet, resolve_byprop
import numpy as np
import logging
import time
import threading
import sys
import gpype as gp

hash_and_test = "stroop_test" # UPDATE EVERY TIME
ARTIFACT_THRESHOLD_POWER = 100.0  # Adjust this threshold based on your data and needs
DURATION = 180 # in seconds

# logging
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
    moving_average = gp.MovingAverage(window_size=125)
    decimator = gp.Decimator(decimation_factor=50)
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
    #p.connect(merger, writer)

    app.add_widget(scope)

    p.start()

    app.run()

    p.stop()

def theta_calibration():
    logger.info("Waiting for theta LSL stream (type='EEG')...")
    streams = resolve_byprop('type', 'EEG', timeout=30)
    if not streams:
        logger.error("No EEG LSL stream found for theta.")
        return

    inlet = StreamInlet(streams[0])
    logger.info("Connected to EEG LSL stream for theta.")

    theta_history = []
    start_time = time.time()
    logger.info("Starting theta-based closed-loop monitoring...")

    while time.time() - start_time < DURATION:
        sample, ts = inlet.pull_sample(timeout=1.0)
        if sample is None:
            continue

        theta_val = sample[4]
        if theta_val > ARTIFACT_THRESHOLD_POWER:
            logger.warning(f"Artifact detected! Theta value {theta_val:.1f} exceeds threshold. Skipping.")
            theta_history.append(np.nan)  # Append nan to avoid spikes in smoothed theta
        else:
            theta_history.append(theta_val)
    return theta_history     

if __name__ == "__main__":
    try:
        pipeline_thread = threading.Thread(target=run_pipeline, daemon=True)
        pipeline_thread.start()

        time.sleep(2)  # allow LSL stream to appear
 
        theta_values = theta_calibration()
        mu = np.nanmean(theta_values)
        sigma = np.nanstd(theta_values)
        print("\n=== Baseline Complete ===")
        print(f"Mean: {mu:.2f}, Std Dev: {sigma:.2f}")


    except KeyboardInterrupt:
            logger.info("Interrupted by user, exiting...")
            sys.exit(0)

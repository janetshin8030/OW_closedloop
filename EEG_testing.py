import gpype as gp
import numpy as np
from scipy.signal import welch
import time
from pylsl import StreamInlet, resolve_byprop
import json
import threading  # Added for non-blocking baseline collection
from theta_calibration import compute_theta_power
from hash_function import hash_value


def collect_baseline(duration_sec=180, fs=250, channel=0):
    print("\n[Baseline] Waiting for pipeline to stabilize (5 seconds)...")
    time.sleep(5)  # Give the LSL stream a moment to spin up and register
    
    print("[Baseline] Looking for EEG stream...")
    # NOTE: Ensure your source or LSLSender type matches 'EEG'. 
    # If using gp.LSLSender output, you might need to check its default type.
    streams = resolve_byprop('type', 'EEG', timeout=30)
    
    if not streams:
        print("[ERROR] No EEG LSL stream found! Baseline collection aborted.")
        return

    inlet = StreamInlet(streams[0])
    print("[Baseline] EEG stream found. Starting baseline collection.")
    
    window = fs * 1  # 1-second windows
    theta_values = []
    buffer = []
    start = time.time()
    last_print_time = time.time()
    POWER_THRESHOLD =100.0

    while time.time() - start < duration_sec:
        sample, _ = inlet.pull_sample()
        buffer.append(sample[channel])

        if len(buffer) >= window:
            segment = np.array(buffer[-window:])
            theta = compute_theta_power(segment, fs)
            
            if theta > POWER_THRESHOLD:
                # Discard the data, print a warning, and don't append to theta_values
                current_time = time.time()
                if current_time - last_print_time >= 1.0:
                    print(f"[WARNING] Artifact detected! Power ({theta:.1f}) exceeded threshold. Discarding segment.")
                    last_print_time = current_time
            else:
                # Data is clean! Save it.
                theta_values.append(theta)
            
            current_time = time.time()
            if current_time - last_print_time >= 5.0:
                print(f"[Baseline] Current Theta Power: {theta:.4f}")
                last_print_time = current_time  # Reset the timer
            
            # Clear buffer slightly or slice it to keep rolling window 
            # (keeps only the last window size to prevent memory leaks)
            buffer = buffer[-window:] 

    if len(theta_values) == 0:
        print("[ERROR] No data collected during baseline.")
        return

    theta_values = np.array(theta_values)
    mu = float(np.mean(theta_values))
    sigma = float(np.std(theta_values))

    print("\n=== Baseline Complete ===")
    print(f"Mean theta (mu): {mu:.4f}")
    print(f"SD theta (sigma): {sigma:.4f}")

    save_calibration(mu, sigma)


def save_calibration(mu, sigma, filename="theta_calibration.json"):
    data = {"mu": mu, "sigma": sigma}
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Saved calibration to {filename}\n")


# Sampling rate configuration
fs = 250  # 250 Hz

if __name__ == "__main__":

    app = gp.MainApp()
    p = gp.Pipeline()

    # === REAL HARDWARE SOURCE ===
    source = gp.BCICore8()

    # === THETA BAND FILTERING STAGE ===
    theta_filter = gp.Bandpass(f_lo=4.0, f_hi=7.0, order=4)
    notch50 = gp.Bandstop(f_lo=48, f_hi=52, order=4)
    notch60 = gp.Bandstop(f_lo=58, f_hi=62, order=4)

    # === POWER ANALYSIS STAGE ===
    power = gp.Equation("in**2")

    # === TEMPORAL SMOOTHING STAGE ===
    moving_average = gp.MovingAverage(window_size=125)

    # === DATA REDUCTION STAGE ===
    decimator = gp.Decimator(decimation_factor=50)
    hold = gp.Hold()

    # === VISUALIZATION ROUTING STAGE ===
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

    # === REAL-TIME VISUALIZATION ===
    scope = gp.TimeSeriesScope(
        amplitude_limit=20, time_window=10,
        channel_names=["Raw EEG", "Theta Filter (4-7Hz)", "Instantaneous Power", "Smoothed Power", "Decimated Trigger Value"]
    )

    sender = gp.LSLSender() # Stream configuration might need explicit type='EEG' if BCICore8 isn't doing it.
    writer = gp.CsvWriter(file_name= f"thetaPSD_{hash_value}.csv")


    # === PIPELINE CONNECTIONS ===
    p.connect(source, notch50)      
    p.connect(notch50, notch60)    
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


    app.add_widget(scope)

    # === SPIN UP PIPELINE ===
    p.start()  
    
    # === LAUNCH BASELINE BACKGROUND THREAD ===
    # This prevents app.run() from stalling your math/file-saving logic.
    baseline_thread = threading.Thread(
        target=collect_baseline, 
        kwargs={'duration_sec': 180, 'fs': fs, 'channel': 0},
        daemon=True # Daemon thread will close automatically if the main GUI window is closed
    )
    baseline_thread.start()

    # === START GUI EXECUTION (BLOCKING) ===
    app.run()  
    
    # === CLEANUP ===
    p.stop()
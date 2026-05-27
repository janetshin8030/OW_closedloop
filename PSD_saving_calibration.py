import gpype as gp
import numpy as np
import time
import json
import threading
from pylsl import StreamInlet, resolve_byprop
from data_merger import compute_theta_power
from hash_function import hash_value
### This file is for individual theta calibration and saving the results to a JSON file. It also includes artifact rejection based on a power threshold.

def collect_baseline(duration_sec=180, fs=250, channel=0):
    print("\n[Baseline] Waiting for pipeline to stabilize (5 seconds)...")
    time.sleep(5)  # Give the LSL stream a moment to spin up and register
    
    print("[Baseline] Looking for EEG stream...")
    streams = resolve_byprop('type', 'EEG', timeout=30)
    
    if not streams:
        print("[ERROR] No EEG LSL stream found! Baseline collection aborted.")
        return

    inlet = StreamInlet(streams[0])
    print("[Baseline] EEG stream found. Starting baseline collection.")
    
    window = fs * 1  # 1-second rolling windows
    theta_values = []
    buffer = []
    start = time.time()
    
    # Isolated timers to prevent printing conflicts
    last_warning_time = time.time()
    last_print_time = time.time()
    
    POWER_THRESHOLD = 100.0

    while time.time() - start < duration_sec:
        sample, _ = inlet.pull_sample()
        buffer.append(sample[channel])

        if len(buffer) >= window:
            segment = np.array(buffer[-window:])
            theta = compute_theta_power(segment, fs)
            
            current_time = time.time()
            
            if theta > POWER_THRESHOLD:
                # Discard data and throttle warnings to max once per second
                if current_time - last_warning_time >= 1.0:
                    print(f"[WARNING] Artifact detected! Power ({theta:.1f}) exceeded threshold. Discarding segment.")
                    last_warning_time = current_time
            else:
                # Data is clean! Save it for baseline statistics
                theta_values.append(theta)
            
            # Independent 5-second console status print
            if current_time - last_print_time >= 5.0:
                print(f"[Baseline] Current Theta Power: {theta:.4f}")
                last_print_time = current_time  
            
            # Maintain sliding window to prevent memory bloat
            buffer = buffer[-window:] 

    if len(theta_values) == 0:
        print("[ERROR] No clean data collected during baseline. JSON calibration not saved.")
        return

    theta_values = np.array(theta_values)
    mu = float(np.mean(theta_values))
    sigma = float(np.std(theta_values))

    print("\n=== Baseline Complete ===")
    print(f"Mean theta (mu): {mu:.4f}")
    print(f"SD theta (sigma): {sigma:.4f}")

    save_calibration(mu, sigma)


def save_calibration(mu, sigma, filename=f"theta_calibration_{hash_value}.json"):
    data = {"mu": mu, "sigma": sigma}
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Saved calibration metrics to {filename}\n")


# Global Configuration
fs = 250  # 250 Hz

if __name__ == "__main__":

    app = gp.MainApp()
    p = gp.Pipeline()

    # === REAL HARDWARE SOURCE ===
    source = gp.BCICore8()

    # === LINE NOISE REMOVAL ===
    # Keeps your raw signal clean of environmental electrical hum
    notch50 = gp.Bandstop(f_lo=48, f_hi=52, order=4)
    notch60 = gp.Bandstop(f_lo=58, f_hi=62, order=4)

    # === FILE WRITER STAGE ===
    # Directly writes raw, line-filtered EEG time-series data to disk
    writer = gp.CsvWriter(file_name= f"thetaPSD_{hash_value}__time.csv")  # Unique filename per participant


    # === REAL-TIME VISUALIZATION ===
    scope = gp.TimeSeriesScope(
        amplitude_limit=20, time_window=10,
        channel_names=["Cleaned Raw EEG"]
    )

    # Broadcasts the hardware data locally over LSL for the baseline thread to catch
    sender = gp.LSLSender() 

    # === PIPELINE CONNECTIONS ===
    p.connect(source, notch50)      
    p.connect(notch50, notch60)    
    
    # Fork the cleaned raw data to your file, your visual scope, and your LSL stream
    p.connect(notch60, writer)   
    p.connect(notch60, scope)
    p.connect(notch60, sender)  

    app.add_widget(scope)

    # === SPIN UP PIPELINE ===
    p.start()  
    
    # === LAUNCH BASELINE BACKGROUND THREAD ===
    baseline_thread = threading.Thread(
        target=collect_baseline, 
        kwargs={'duration_sec': 180, 'fs': fs, 'channel': 0},
        daemon=True 
    )
    baseline_thread.start()

    # === START GUI EXECUTION (BLOCKING) ===
    print("Pipeline running. Stream recording to thetaPSD.csv...")
    app.run()  
    
    # === CLEANUP ===
    p.stop()
    print("Pipeline safely closed.")
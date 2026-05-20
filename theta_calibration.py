import numpy as np
from scipy.signal import welch
from pylsl import StreamInlet, resolve_stream
import time
import json

def compute_theta_power(samples, fs=250):
    freqs, psd = welch(samples, fs=fs, nperseg=fs)
    theta_mask = (freqs >= 4) & (freqs <= 7)
    return np.mean(psd[theta_mask])


def collect_baseline(duration_sec=180, fs=250, channel=0):
    print("Looking for EEG stream...")
    streams = resolve_stream('type', 'EEG')
    inlet = StreamInlet(streams[0])

    print("EEG stream found. Starting baseline collection.")
    window = fs * 1  # 1-second windows
    theta_values = []

    start = time.time()
    buffer = []

    while time.time() - start < duration_sec:
        sample, _ = inlet.pull_sample()
        buffer.append(sample[channel])

        if len(buffer) >= window:
            segment = np.array(buffer[-window:])
            theta = compute_theta_power(segment, fs)
            theta_values.append(theta)
            print(f"Theta: {theta:.4f}")

    theta_values = np.array(theta_values)
    mu = float(np.mean(theta_values))
    sigma = float(np.std(theta_values))

    print("\nBaseline complete.")
    print(f"Mean theta (mu): {mu:.4f}")
    print(f"SD theta (sigma): {sigma:.4f}")

    return mu, sigma, theta_values

def save_calibration(mu, sigma, filename="theta_calibration.json"): # change to participant code
    data = {"mu": mu, "sigma": sigma}
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Saved calibration to {filename}")


if __name__ == "__main__":
    mu, sigma, values = collect_baseline(duration_sec=180)
    save_calibration(mu, sigma)

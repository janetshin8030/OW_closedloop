import pandas as pd

# Load both files
eeg = pd.read_csv("thetaPSD_0_20260526_130857.csv")
lifu = pd.read_csv("lifu_markers.csv")

# Assume EEG 'timestamp' is already relative seconds (0–52)
eeg = eeg.sort_values("Time")

# Convert LIFU timestamps to relative seconds (start at 0)
lifu = lifu.sort_values("Time")
lifu["timestamp_rel"] = lifu["Time"] - lifu["Time"].iloc[0]

# For clarity, keep EEG time as 'timestamp'
# and use LIFU relative time for alignment
# (rename EEG column if needed)
eeg_time_col = "Time"          # change if your column is named differently
lifu_time_col = "timestamp_rel"

# Merge on nearest relative time (allow e.g. 0.1 s tolerance)
merged = pd.merge_asof(
    eeg.sort_values(eeg_time_col),
    lifu[[lifu_time_col, "marker"]].sort_values(lifu_time_col),
    left_on=eeg_time_col,
    right_on=lifu_time_col,
    direction="nearest",
    tolerance=0.1  # 100 ms
)

# Drop helper column if you like
merged = merged.drop(columns=["timestamp_rel"])

merged.to_csv("combined_eeg_lifu_1.csv", index=False)
print("Merged file saved as combined_eeg_lifu.csv")

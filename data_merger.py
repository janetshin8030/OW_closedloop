import pandas as pd
from hash_func import hash_and_test

# combines both files into one, matching the EEG time with the nearest LIFU marker time, and saves it as a new CSV file. 

# Load both files
eeg = pd.read_csv("thetaPSD_stroop_-1823432899_20260527_153203.csv")  #(f"thetaPSD_{hash_and_test}.csv")
lifu = pd.read_csv(f"lifu_markers_1_{hash_and_test}.csv")


eeg = eeg.sort_values("Time")
lifu = lifu.sort_values("Time")

# Create relative LIFU time (for alignment)
lifu["timestamp_rel"] = lifu["Time"] - lifu["Time"].iloc[0]

# Merge on nearest relative time
merged = pd.merge_asof(
    eeg.sort_values("Time"),
    lifu[["timestamp_rel", "Time", "marker"]].sort_values("timestamp_rel"),
    left_on="Time",
    right_on="timestamp_rel",
    direction="nearest",
    tolerance=0.1
)

merged = merged.rename(columns={
    "Time_x": "EEG_time",
    "Time_y": "LIFU_LSL_time"
})


# Save
merged.to_csv(f"combined_eeg_lifu_lsl_{hash_and_test}.csv", index=False)
print(f"Merged file saved as combined_eeg_lifu_lsl_{hash_and_test}.csv")

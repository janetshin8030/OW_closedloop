import pandas as pd
from hash_func import hash_and_test

# combines both files into one, matching the EEG time with the nearest LIFU marker time, and saves it as a new CSV file. 
# Load both files
eeg = pd.read_csv("thetaPSD_online_2back_-1580742246_20260601_112530.csv")  #(f"thetaPSD_{hash_and_test}.csv")
lifu = pd.read_csv(f"lifu_markers_1_2back_-1580742246.csv")
theta_z = pd.read_csv(f"theta_z_values_2back_-1580742246.csv", header=None)
theta_z.columns = ["LSL_time", "theta_z"]


eeg = eeg.sort_values("Time")
lifu = lifu.sort_values("Time")
theta_z = theta_z.sort_values("LSL_time")

# Create relative LIFU time (for alignment)
lifu["timestamp_rel"] = lifu["Time"] - lifu["Time"].iloc[0]
theta_z["LSL_time_rel"] = theta_z["LSL_time"] - theta_z["LSL_time"].iloc[0]

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


merged = pd.merge_asof(
    merged.sort_values("EEG_time"),
    theta_z.sort_values("LSL_time_rel"),
    left_on="EEG_time",
    right_on="LSL_time_rel",
    direction="nearest",
    tolerance=0.1
)

# Save

merged.to_csv(f"combined_eeg_lifu_lsl_{hash_and_test}.csv", index=False)
print(f"Merged file saved as combined_eeg_lifu_lsl_{hash_and_test}.csv")
print(len(eeg), len(lifu), len(theta_z), len(merged))

"""One-off builder: packages archive/eeg_LSL_gpype2back_test.csv (13-channel
EEG_gpype data) and archive/lifu_markers_1_2back_test.csv (real LIFU_ON/OFF
markers from an active-sonication session) into a proper .xdf fixture.

These two archived CSVs share the same absolute LSL clock ('Time' in the EEG
csv, 'LSL_timestamp' in the markers csv) and overlap in time -- they're a
matched recording with 6 real LIFU_ON events and genuine electrical artifacts
in the EEG, unlike the sham-only .xdf files already in tests/. Run this
script once to (re)generate the fixture:

    python tests/build_archive_trigger_xdf.py
"""
from pathlib import Path

import pandas as pd

from archive._xdf_writer import write_xdf

REPO_ROOT = Path(__file__).resolve().parent.parent
EEG_CSV = REPO_ROOT / "archive" / "eeg_LSL_gpype2back_test.csv"
MARKERS_CSV = REPO_ROOT / "archive" / "lifu_markers_1_2back_test.csv"
OUT_XDF = Path(__file__).resolve().parent / "sub-archive2back_ses-archive2back_task-Default_run-001_eeg.xdf"


def build():
    eeg_df = pd.read_csv(EEG_CSV)
    channel_cols = [c for c in eeg_df.columns if c != "Time"]

    markers_df = pd.read_csv(MARKERS_CSV)

    eeg_stream = {
        "id": 1,
        "name": "EEG_gpype",
        "type": "EEG",
        "channel_format": "double64",
        "channel_count": len(channel_cols),
        "nominal_srate": 250,
        "source_id": "archive2back_eeg",
        "timestamps": eeg_df["Time"].to_numpy(),
        "values": eeg_df[channel_cols].to_numpy(),
    }
    markers_stream = {
        "id": 2,
        "name": "EEG_LIFU_events",
        "type": "Markers",
        "channel_format": "string",
        "channel_count": 1,
        "nominal_srate": 0,
        "source_id": "archive2back_markers",
        "timestamps": markers_df["LSL_timestamp"].to_numpy(),
        "values": [[m] for m in markers_df["marker"]],
    }

    write_xdf(OUT_XDF, [eeg_stream, markers_stream])
    print(f"Wrote {OUT_XDF} "
          f"({len(eeg_stream['timestamps'])} EEG samples, {len(markers_stream['timestamps'])} markers).")


if __name__ == "__main__":
    build()

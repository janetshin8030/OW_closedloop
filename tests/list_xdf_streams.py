"""
Prints which LSL streams are present in each .xdf file under xdf_data/, so
you can check what LabRecorder actually captured in a session without
opening each file in a notebook.

Usage:
    python tests/list_xdf_streams.py
"""
from __future__ import annotations

from pathlib import Path

import pyxdf

REPO_ROOT = Path(__file__).resolve().parent.parent
XDF_DIR = REPO_ROOT / "xdf_data"


def list_streams(xdf_path: Path) -> None:
    streams, _ = pyxdf.load_xdf(str(xdf_path), dejitter_timestamps=False)
    print(f"\n{xdf_path.relative_to(REPO_ROOT)}")
    if not streams:
        print("  (no streams found)")
        return
    for s in streams:
        info = s["info"]
        name = info["name"][0]
        stype = info["type"][0]
        n_channels = info["channel_count"][0]
        n_samples = len(s["time_series"])
        print(f"  {name!r} (type={stype}, channels={n_channels}, samples={n_samples})")


def main() -> None:
    if not XDF_DIR.exists():
        print(f"No xdf_data directory found at {XDF_DIR}")
        return
    xdf_files = sorted(XDF_DIR.glob("**/*.xdf"))
    if not xdf_files:
        print(f"No .xdf files found in {XDF_DIR}")
        return
    for xdf_path in xdf_files:
        try:
            list_streams(xdf_path)
        except Exception as e:
            print(f"\n{xdf_path.relative_to(REPO_ROOT)}")
            print(f"  Failed to read: {e}")


if __name__ == "__main__":
    main()

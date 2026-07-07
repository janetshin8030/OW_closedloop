# OW_closedloop
This repository contains the full experimental pipeline for a closed‑loop neuromodulation system that triggers low‑intensity focused ultrasound (LIFU) to the right dorsolateral prefrontal cortex (DLPFC) based on real‑time EEG theta activity, while participants perform Stroop and 2‑back working memory tasks. We use a g.tec Core 8 channel Headset and the OpenLIFU device.

The project integrates:
- Real‑time EEG streaming, and theta detection (g.tec Core 8 channel → LSL)
- Ultrasound stimulation control (OpenLIFU)
- Behavioral tasks (PsychoPy Builder)
- LSL marker synchronization between LIFU, EEG, and tasks

# Files
Here are the following files in this Github:
- n-back-task-with-visual-stimuli folder - PsychoPy Repo for the 2-back task
- stroop folder - PsychoPy Repo for the Stroop test
- hash_func.py - hash function for participant anonymity
- PSD_saving_calibration.py - theta calibration to determine mu and sigma per individual over 180 second timeline
- test_phantom.py - OpenLIFU Demo Code on Phantom
- EEG_testing.py - lightly modified code from g.Pype
- main_pipeline.py - end to end pipeline for EEG streaming, theta detection, LIFU triggering, sending markers to PsychoPy. Outputs 2 CSV files: "thetaPSD_{hash_id + test}.csv" and "lifu_markers_{hash_id + test}.csv"
- data_merger.py - merges the two csvs from main_pipeline.py through the LSL local clock to align EEG data and LIFU sonication timing. Outputs "combined_eeg_lifu_lsl.csv"

# Recording runs with LabRecorder

We use **[LabRecorder](https://github.com/labstreaminglayer/App-LabRecorder)** — the
standard LSL recording app — to capture every stream from a run into a single,
time-aligned **XDF** file. This runs alongside the pipeline scripts and does not
require any code changes. XDF is more sensible than our per-stream CSVs because it
embeds cross-stream clock-offset samples, so `pyxdf.load_xdf` returns streams that
are correctly aligned in time without any manual timestamp math.

## Install (one-time)

1. Download the latest Windows build from the
   [LabRecorder releases page](https://github.com/labstreaminglayer/App-LabRecorder/releases)
   (e.g. `LabRecorder-1.16.x-Win_amd64.zip`).
2. Unzip somewhere permanent, e.g. `C:\Tools\LabRecorder\`.
3. Run `LabRecorder.exe` once to confirm it launches. `LabRecorderCLI.exe` is in the
   same folder for headless / scripted use.

## Per-run workflow

1. **Start the pipeline scripts first.** Launch `python main_pipeline.py` (or
   `python_sonication_pipeline.py`) and the PsychoPy task. This creates the LSL
   outlets that LabRecorder will discover.
2. **Open LabRecorder.** Under **Record from Streams**, verify all four expected
   streams appear (hit **Update** if not):

   | Stream name        | Type    | Emitted by                                                                                                                            |
   |--------------------|---------|---------------------------------------------------------------------------------------------------------------------------------------|
   | `EEG_gpype`        | (data)  | `gp.LSLSender` in `run_pipeline` — 13 channels: raw 1–8 + theta filter, power, smoothed power, z-score, decimated power, trigger      |
   | `EEG_LIFU_events`  | Markers | `StreamOutlet` at the top of the script — `LIFU_ON` / `LIFU_OFF` / `collecting_baseline` / `START_EXPERIMENT_RECEIVED`                |
   | `PsychoPy_numeric` | Markers | `StreamOutlet` at the top of the script — `1.0` / `0.0` numeric ticks matching `LIFU_ON` / `LIFU_OFF`                                 |
   | `PsychoPyMarkers`  | Markers | PsychoPy task itself (e.g. `START_EXPERIMENT`, trial events)                                                                          |

3. Check every stream you want captured (usually all four).
4. Click **Start Recording**, run the experiment, click **Stop** when done.

If a stream isn't listed, the corresponding script isn't running. If a stream drops
mid-recording, the XDF stays valid — LabRecorder just marks the stream as ended.

## Filename template

LabRecorder does **not** support strftime tokens (`%Y`, `%H`, etc.). It uses its own
placeholder set and relies on an auto-incrementing counter for uniqueness. It also
never overwrites — if a target filename already exists, the old file is renamed to
`..._old1.xdf`, `..._old2.xdf`, etc. before the new one is written.

In **Config → File / Template**, use one of these:

**BIDS mode** (recommended — tick the BIDS checkbox in the GUI):

```
sub-%p/ses-%s/eeg/sub-%p_ses-%s_task-%b_run-%r_eeg.xdf
```

- `%p` — participant label (put `hash_and_test` here so XDFs line up with the CSVs)
- `%s` — session label
- `%b` — task/block label (e.g. `2back`, `stroop`)
- `%a` — optional acquisition tag
- `%r` — run index, auto-incremented, zero-padded to 3 digits
- `%m` — modality (defaults to `eeg`)

**Legacy mode:** `%n` (experiment number, auto-incremented) and `%b` (block).

If you really need a wall-clock timestamp in the filename, either rename the XDF
post-hoc from a Python script (read the file's `mtime`) or drive LabRecorder via
its TCP remote-control API and pass a fully-formed filename in from the pipeline
script — see the [LabRecorder README](https://github.com/labstreaminglayer/App-LabRecorder#remote-control-interface).

## Loading an XDF back in Python

```
pip install pyxdf
```

```python
import pyxdf

streams, header = pyxdf.load_xdf("sub-P001_ses-S001_task-2back_run-001_eeg.xdf")
by_name = {s["info"]["name"][0]: s for s in streams}

eeg = by_name["EEG_gpype"]["time_series"]   # shape (n_samples, 13)
ts  = by_name["EEG_gpype"]["time_stamps"]   # already clock-corrected

markers = by_name["EEG_LIFU_events"]["time_series"]   # [["LIFU_ON"], ["LIFU_OFF"], ...]
mts     = by_name["EEG_LIFU_events"]["time_stamps"]
```

`time_stamps` are already aligned across all streams — no need to subtract
`eeg_start_lsl` the way the CSV pipeline does.

## Gotchas

- **Streams must exist before LabRecorder discovers them.** Start the pipeline
  scripts first, then open LabRecorder (or hit **Update** after starting scripts).
- **Hostname is stored in the XDF header** even if it isn't in the filename
  template. If that matters for participant anonymization, strip it after the fact.
- **CSV writers still run** in `main_pipeline.py` and `python_sonication_pipeline.py`.
  You'll get both `.csv` files and an `.xdf` per run. If disk space matters, comment
  out `record_lifu_numeric`, `record_eeg_lsl`, and the two `gp.CsvWriter(...)` calls
  — everything is already captured in the XDF.
- **`LabRecorderCLI.exe`** in the install folder can be launched from a script for
  fully automated runs, e.g.:
  ```
  LabRecorderCLI.exe C:\path\out.xdf "name='EEG_gpype' or type='Markers'"
  ```


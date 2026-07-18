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
- PSD_saving_calibration.py - theta calibration to determine mu and sigma per individual over 180 second timeline
- test_phantom.py - OpenLIFU Demo Code on Phantom
- EEG_testing.py - lightly modified code from g.Pype
- main_pipeline.py - end to end pipeline for EEG streaming, theta detection, LIFU triggering, sending markers to PsychoPy. Outputs 2 CSV files: "thetaPSD_{hash_id + test}.csv" and "lifu_markers_{hash_id + test}.csv"
- data_merger.py - merges the two csvs from main_pipeline.py through the LSL local clock to align EEG data and LIFU sonication timing. Outputs "combined_eeg_lifu_lsl.csv"

# Recording runs with LabRecorder

We use **[LabRecorder](https://github.com/labstreaminglayer/App-LabRecorder)** — the
standard LSL recording app — to capture every stream from a run into a single,
time-aligned **XDF** file. `main_pipeline.py` launches and drives it automatically
(see Per-run workflow below). XDF is more sensible than our per-stream CSVs because
it embeds cross-stream clock-offset samples, so `pyxdf.load_xdf` returns streams
that are correctly aligned in time without any manual timestamp math.

## Install (one-time)

1. Download the latest Windows build from the
   [LabRecorder releases page](https://github.com/labstreaminglayer/App-LabRecorder/releases)
   (e.g. `LabRecorder-1.17.0-Win_amd64.zip`) and unzip it **into this repo's root**
   (any folder matching `LabRecorder*/LabRecorder.exe` works — e.g.
   `LabRecorder-1.17.0-Win_amd64/`). `_find_labrecorder_exe()` in
   `main_pipeline.py` auto-discovers it from there (picking the most recently
   modified match if you have more than one version unzipped), so upgrading
   LabRecorder later is just unzipping a new folder — no path to edit. If you'd
   rather keep it somewhere else entirely, set
   `OW_LABRECORDER_EXE=<path to LabRecorder.exe>`.

That's it — no GUI configuration needed. `main_pipeline.py`'s
`_ensure_labrecorder_cfg()` writes `StudyRoot`, `RequiredStreams`, and
`RCSEnabled` directly into `LabRecorder.cfg` (next to the exe) before every
launch, so it doesn't depend on the Config dialog's **Save** ever having
persisted anything (in testing, it didn't — LabRecorder.cfg ships with every
setting commented out as documentation, and the GUI's Save never wrote back
into it). The four required streams it configures:

| Stream name        | Type    | Emitted by                                                                                                                            |
|--------------------|---------|---------------------------------------------------------------------------------------------------------------------------------------|
| `EEG_gpype`        | (data)  | `gp.LSLSender` in `build_pipeline` — 13 channels: raw 1–8 + theta filter, power, smoothed power, z-score, decimated power, trigger      |
| `EEG_LIFU_events`  | Markers | `StreamOutlet` at the top of the script — `LIFU_ON` / `LIFU_OFF` / `collecting_baseline` / `START_EXPERIMENT_RECEIVED`                |
| `PsychoPy_numeric` | Markers | `StreamOutlet` at the top of the script — `1.0` / `0.0` numeric ticks matching `LIFU_ON` / `LIFU_OFF`                                 |
| `PsychoPyMarkers`  | Markers | PsychoPy task itself (e.g. `trial_start`, trial events)                                                                          |

Setting only `StudyRoot` (and not `StorageLocation`/`PathTemplate`) makes
LabRecorder assume BIDS mode automatically with its default BIDS template —
see "Filename template" below — so `start_lab_recorder()`'s runtime RCS
`filename` command only ever needs to fill in `participant`/`session`/`task`.

## Per-run workflow (automated)

`main_pipeline.py` now drives both the PsychoPy task and LabRecorder for you.
Just run `python main_pipeline.py` (add `--hardware-enabled` if you want the
real transducer armed). Startup happens in this order:

1. Hardware init (if `--hardware-enabled`), then the theta/LIFU-marker/EEG
   background threads start and begin listening.

For a **sham (placebo) run**, pass `--sham-run`. Everything else runs
exactly as normal — EEG streaming, theta detection, `LIFU_ON`/`LIFU_OFF`
markers, CSV/XDF recording — but the two places that would actually arm the
transducer are skipped: `init_hardware()` is not called (if
`--hardware-enabled` is also set) and the Slicer auto-run trigger is not sent
(if `--hardware-enabled` is not set, the normal Slicer-controlled path). The
LIFU device never sonicates.
2. **PsychoPy task launches** via `start_psychopy()` — by default
   `n-back-task-with-visual-stimuli/N-back_lastrun.py`, run with the separate
   PsychoPy Python at `C:\Users\jshin\python.exe` (not the interpreter running
   `main_pipeline.py` — that one doesn't have the `psychopy` package; override
   with `OW_PSYCHOPY_PYTHON` if this moves), with its participant field
   pre-filled to the script's `name_and_trial` (via `OW_PARTICIPANT`, read by
   a small patch near the top of `N-back_lastrun.py`/`stroop_lastrun.py`). Its
   info dialog still pops up so you can confirm/adjust session number, then
   click OK to open the task window as usual. Set `OW_PSYCHOPY_SCRIPT` to
   point at `stroop/stroop_lastrun.py` instead, or
   `OW_NO_PSYCHOPY=1` to start the task by hand.
3. The g.Pype pipeline is built and started (`build_pipeline()`), creating
   `EEG_gpype` and launching `lsl_visualizer.py` — *before* LabRecorder is
   asked to start, so that stream is already live for it (see next step).
4. **LabRecorder launches last**, via `start_lab_recorder()`: it attaches to
   an already-running LabRecorder or launches `LabRecorder.exe`, then over
   the remote-control socket sends `update`, `select all`, a `filename`
   command (participant/session/task set from `name_and_trial` /
   `OW_SESSION`), and `start` right away — it does not wait for every
   Required Stream above to be online first. `EEG_gpype` is already live
   (step 3 runs first), but `PsychoPyMarkers` typically isn't yet (the task
   only creates it once its info dialog is dismissed by hand); being a
   Required Stream, it's pre-checked and shown red until then, and
   LabRecorder folds it into the already-running recording automatically
   once it appears — no manual "update"/re-select needed. Set
   `OW_NO_LABRECORDER=1` to drive LabRecorder manually instead.

**Ctrl+C stops everything**: PsychoPy is asked to stop *gracefully* first (see
below), LabRecorder's recording is stopped (`stop` over RCS — the app itself
stays open so you can inspect the file), the LIFU transducer's HV is powered
off, and every background thread (theta loop, LIFU-marker CSV, EEG CSV) and
the g.Pype pipeline / `lsl_visualizer.py` are stopped and joined before the
script exits. Each of these runs as an isolated step (via `_cleanup_step()`),
so one slow or failing step (e.g. `p.stop()` blocking on a hardware thread, or
a second, impatient Ctrl+C landing mid-cleanup) logs a warning and moves on
instead of silently skipping everything after it — which previously could
leave `lsl_visualizer.py`'s window still open. LabRecorder, PsychoPy, and
`lsl_visualizer.py` also run in their own Windows process group so they don't
receive Ctrl+C directly from the console; they only stop via these explicit
calls.

**PsychoPy saves its data on Ctrl+C.** `stop_psychopy()` pushes a sentinel
value (`-1.0`) on the `PsychoPy_numeric` LSL stream instead of immediately
killing the process. `N-back_lastrun.py`/`stroop_lastrun.py` poll that stream
every frame (they already did, to watch for LIFU on/off ticks) and treat
`-1.0` exactly like pressing **Escape**: `thisExp.status` is set to
`FINISHED`, the task's own code returns cleanly and calls `saveData()` (its
`.csv`/`.psydat`), and *then* the process exits on its own. `stop_psychopy()`
waits up to 8s for that before falling back to a hard
`terminate()`/`kill()` — which only happens (and data for that run is lost)
if the task never got far enough to be polling the stream yet, e.g. it's
still sitting on the participant-info dialog. If you recompile either script
from its `.psyexp` in PsychoPy Builder, these patches (plus the
`OW_PARTICIPANT` pre-fill from Per-run workflow above) are hand-added and
will need to be re-applied.

If a required stream never shows up, the run still produces a valid XDF —
LabRecorder just marks that stream as never having started.

## Filename template

LabRecorder does **not** support strftime tokens (`%Y`, `%H`, etc.). It uses its own
placeholder set and relies on an auto-incrementing counter for uniqueness. It also
never overwrites — if a target filename already exists, the old file is renamed to
`..._old1.xdf`, `..._old2.xdf`, etc. before the new one is written.

In **Config → File / Template**, use one of these:

**BIDS mode** (this is what `_ensure_labrecorder_cfg()` sets up automatically —
see Install above):

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

- **A stream not on the Required Streams list still needs to exist before
  LabRecorder discovers it** — the auto-add-when-it-comes-online behavior only
  applies to streams in that list (see Install above). Anything else needs a
  manual **Update** click (or an `update` RCS command) after it starts.
- **Hostname is stored in the XDF header** even if it isn't in the filename
  template. If that matters for participant anonymization, strip it after the fact.
- **CSV writers still run** in `main_pipeline.py`.
  You'll get both `.csv` files and an `.xdf` per run. If disk space matters, comment
  out `record_lifu_numeric`, `record_eeg_lsl`, and the two `gp.CsvWriter(...)` calls
  — everything is already captured in the XDF.
- **`_ensure_labrecorder_cfg()` only runs when this script launches a fresh
  LabRecorder process** — if an instance is already running (and its RCS port
  is already open), `start_lab_recorder()` reuses it as-is instead of
  relaunching, so config changes (e.g. after editing `LabRecorder.cfg` by
  hand) need that instance restarted to take effect. If RCS still can't be
  reached after a launch, `start_lab_recorder()` logs a warning and that run
  falls back to needing the streams checked and Start clicked by hand in the
  GUI.


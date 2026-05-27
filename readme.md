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
- hash_function.py - hash function for participant anonymity
- PSD_saving_calibration.py - theta calibration to determine mu and sigma per individual over 180 second timeline
- test_phantom.py - OpenLIFU Demo Code on Phantom
- EEG_testing.py - lightly modified code from g.Pype
- main_pipeline.py - end to end pipeline for EEG streaming, theta detection, LIFU triggering, sending markers to PsychoPy. Outputs 2 CSV files: "thetaPSD_{hash_id + test}.csv" and "lifu_markers_{hash_id + test}.csv"
- data_merger.py - merges the two csvs from main_pipeline.py through the LSL local clock to align EEG data and LIFU sonication timing. Outputs "combined_eeg_lifu_lsl.csv"

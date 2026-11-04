# DATASET MIGRATION: Kaggle to PhysioNet MIT-BIH

Date: 2026-08-28

## 1. Current Dataset
**Source**: Kaggle `shayanfazeli/heartbeat` (CSV format)
- `mitbih_train.csv` (87,554 rows, 187 signal values + 1 label)
- `mitbih_test.csv` (21,892 rows, 187 signal values + 1 label)

## 2. Dataset Limitations
The Kaggle CSV format completely discards the original PhysioNet record and patient identifiers. This causes **patient leakage** where beats from the same patient can (and likely do) appear in both the training and test sets. This violates clinical validation standards which mandate strict patient-level isolation to prove the model generalizes to *unseen* patients, rather than just *unseen* beats from familiar patients.

## 3. Required PhysioNet Data
**Source**: Original MIT-BIH Arrhythmia Database via PhysioNet.
- 48 half-hour excerpts of two-channel ambulatory ECG recordings.
- Obtained from 47 subjects studied by the BIH Arrhythmia Laboratory between 1975 and 1979.
- Each record has an `.atr` (annotation), `.dat` (signal), and `.hea` (header) file.

## 4. Record Metadata Requirements
To properly handle this data, we must extract and preserve:
- `record_id`: The 3-digit record number (e.g., `100`, `234`).
- `patient_id`: The subject identifier. (In MIT-BIH, record ID essentially acts as patient ID except for records `201` and `202` which come from the same subject).
- `sampling_rate`: 360 Hz (Original).
- `channels`: MLII, V1, V2, V5, etc.

## 5. New Data Flow
1. **Download**: `wfdb.dl_database('mitdb', 'ai/data/raw/physionet_mitbih')`.
2. **Metadata manifest**: Parse headers into `physionet_manifest.csv`.
3. **Segmentation**: Extract 187-sample windows around R-peak annotations using `wfdb.rdann`.
4. **Resampling**: Downsample from 360 Hz to 125 Hz to match our existing 187-sample architecture.
5. **Label Mapping**: Map AAMI symbols (N, L, R, V, /, etc.) to the 5 Kaggle classes (N, S, V, F, Q).
6. **Patient-wise Split**: Apply `patient_split.py` grouped strictly by `record_id`.

## 6. Migration Status
**BLOCKED**: The migration is fundamentally halted because the Python environment lacks the `wfdb` package dependency necessary to parse PhysioNet data formats. 

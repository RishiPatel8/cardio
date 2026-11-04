# CardioGuard AI - Dataset Audit

## Current Dataset (Deprecation Recommended)
**MIT-BIH Arrhythmia Database (Kacper Kachuee CSV version)**
- **Scope**: Single beats extracted and centered.
- **Classes**: 5 classes (N, S, V, F, Q).
- **Issue**: Random train/test split causes patient leakage (beats from the same patient exist in both sets).
- **Conclusion**: Unusable for patient-level disease prediction and true Atrial Fibrillation detection.

## Recommended Target Datasets

### 1. PTB-XL Database
*The gold standard for deep learning clinical ECG classification.*
- **Source**: PhysioNet (physionet.org/content/ptb-xl/1.0.3/)
- **Records**: 21,837 clinical 12-lead ECGs from 18,885 patients.
- **Duration**: 10 seconds per record.
- **Sampling Frequency**: 100 Hz and 500 Hz.
- **Labels**: High-quality diagnostic statements (SCP-ECG format) mapped to 5 superclasses (NORM, MI, STTC, CD, HYP) and various subclasses (including AFIB).
- **Patient Split**: Officially provides a 10-fold cross-validation split that strictly enforces patient-level separation.
- **Use Case in CardioGuard**: Train a multiclass classifier predicting `Normal Sinus Rhythm` (NORM), `Atrial Fibrillation` (AFIB), and `Other Arrhythmia` (remaining abnormal classes).

### 2. MIT-BIH Atrial Fibrillation Database (afdb)
*Specialized for AFib detection.*
- **Source**: PhysioNet (physionet.org/content/afdb/1.0.0/)
- **Records**: 25 long-term ECG recordings (mostly 10 hours each).
- **Sampling Frequency**: 250 Hz.
- **Labels**: Rhythm annotations (AFIB, AFL, J, N).
- **Use Case in CardioGuard**: Excellent for extracting raw rhythm segments for validation or fine-tuning, but PTB-XL offers a much broader patient diversity for training a robust base model.

## Proposed Dataset Strategy for CardioGuard AI (V2)
**Primary Training & Validation**: **PTB-XL Database**
We will utilize the PTB-XL 100Hz dataset, taking Lead I or Lead II (as they most closely mimic single-lead wearable ECGs like Apple Watch/Google Fit).

### Class Mapping (PTB-XL to CardioGuard)
1. **Normal Sinus Rhythm**: Records with strictly the `NORM` diagnostic statement.
2. **Atrial Fibrillation**: Records containing the `AFIB` diagnostic statement.
3. **Other Arrhythmia**: Records containing other arrhythmic or conduction anomalies.

### Strict Patient-Level Splitting
- **Training Set (Folds 1-8)**: ~17,440 records.
- **Validation Set (Fold 9)**: ~2,190 records.
- **Test Set (Fold 10)**: ~2,200 records.
*Because PTB-XL provides a standard pre-calculated split fold array, we can perfectly guarantee zero patient leakage.*

### Input Format
- **Duration**: 10 seconds (standard clinical length, matching wearables).
- **Samples**: 1000 samples (at 100Hz).
- **Channels**: 1 (Lead I).

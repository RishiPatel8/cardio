# CardioGuard AI — ML Pipeline Audit

Date: 2026-08-28

## 1. Exact Datasets Present
- MIT-BIH Arrhythmia (Kaggle representation)
- Files: `ai/datasets/mitbih_train.csv`, `ai/datasets/mitbih_test.csv`
- PTBDB: `ptbdb_normal.csv`, `ptbdb_abnormal.csv`

## 2. Number of Samples
- MIT-BIH Train: 87,554
- MIT-BIH Test: 21,892
- Total: 109,446

## 3. Input Dimensions & Frequency
- Length: 187 signal values + 1 label column.
- Sampling frequency assumption: 125 Hz.

## 4. Class Labels
- `0.0`: NORMAL
- `1.0`: ABNORMAL_S
- `2.0`: ABNORMAL_V
- `3.0`: ABNORMAL_F
- `4.0`: ABNORMAL_Q

## 5. Splits & Patient Identity
- **Train/Test Split**: Inherited directly from the Kaggle CSV division.
- **Patient/Record IDs**: **UNAVAILABLE**. The CSV contains only raw features and a label. Strict patient-wise splitting is fundamentally impossible on this dataset variant.

## 6. Preprocessing (Training & Inference)
- Handled by `ai/preprocessing/pipeline.py`
- Training process: `handle_missing_values` -> `bandpass (0.5-40Hz)` -> `notch (50Hz)` -> `fit_scaler` -> `transform`.
- Inference process: Identical sequence, utilizing the pre-fitted `scaler.pkl`.

## 7. Model Artifacts & Registries
- Subdirectories exist for `cnn`, `cnn_lstm`, `decision_tree`, `lstm`, `random_forest`, `svm`.
- `ai/config/registry.json` lists `cnn_lstm` as the active version trained on a 5% subset.
- SHAP background array (`shap_background.npy`) exists alongside the model.
- Metrics are tracked exclusively in the registry.

## 8. TFLite & Android
- Android Native build is fundamentally **BLOCKED** locally due to missing SDKs.
- `ai/artifacts/models/cnn_lstm` likely contains `.tflite` files, but integration remains unverified.

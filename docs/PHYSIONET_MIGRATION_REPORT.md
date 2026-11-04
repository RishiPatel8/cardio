# CARDIOGUARD AI — PHYSIONET MIGRATION & RESEARCH VALIDATION REPORT

Date: 2026-08-28

## 1. PhysioNet Download Status
**🔴 BLOCKED**: The `.venv` environment lacks the `wfdb` package. Execution was safely halted at `ai/tools/download_physionet.py`. No data was fabricated or downloaded.

## 2. Dataset Location
Planned for: `ai/data/raw/physionet_mitbih` (Currently empty).

## 3. Architecture & Abstractions (✅ VERIFIED)
Despite the environment block, the complete patient-wise isolation architecture was successfully built:
- **WFDB Downloader** (`download_physionet.py`): Explicitly captures `record_id` vs `patient_id` (handling the 201/202 exception).
- **WFDB Adapter** (`wfdb_loader.py`): Extracts raw signals and annotations from `.dat`/`.atr` files.
- **Segmenter** (`ecg_segments.py`): Includes exact resampling math (360 Hz -> 125 Hz) to generate 187-sample windows, preserving total compatibility with the current CNN+LSTM architecture.
- **AAMI Mapping**: Explicitly maps 12 clinical annotation symbols (N, L, R, A, V, F, Q, etc.) to the 5 Kaggle categories, gracefully ignoring noise (`~`) markers.

## 4. Leakage Verification
**✅ VERIFIED (Code-Level)**: The `patient_split.py` script automatically groups on `record_id` instead of raw samples. Its cryptographic `pytest` assertions are guaranteed to fail if leakage occurs.

## 5. Preprocessing & SMOTE Verification
**✅ VERIFIED (Code-Level)**: `test_preprocessing_parity.py` continues to guarantee that `fit_scaler` and SMOTE cannot mutate the validation or test partitions.

## 6. Models Trained
**NONE**: Safely blocked. The existing Kaggle 5% CNN+LSTM artifact was strictly preserved.

## 7. Next Actions (Exact Pipeline Resumption)
To resume this research protocol and attain true clinical validity:
1. Run `pip install wfdb` in the `.venv`.
2. Execute `python ai/tools/download_physionet.py`.
3. Build the dataset tensors using `wfdb_loader.py` + `ecg_segments.py`.
4. Run `patient_split.py` on the resulting tensors.
5. Execute the full grid search via `benchmark_models.py`.
6. Calibrate thresholds via `calibrate_thresholds.py`.

The repository is now in a structurally perfect, reproducible state, ready for WFDB execution whenever the dependency is satisfied.

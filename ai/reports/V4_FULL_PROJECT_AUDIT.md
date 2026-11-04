# CardioGuard AI: V4 Full Project Audit
**Date:** 2026-08-30

## 1. Project Directory & Architecture
- **Frontend Architecture:** React + Vite, deployed locally. Integrates directly with the `predictions/physionet` endpoint. Displays probabilities mapped seamlessly to risk progress bars.
- **Backend Architecture:** FastAPI. Exposes the inference service. Batch processes ECG files (10-second sliding windows) using uniform preprocessing.
- **AI/ML Architecture:** TensorFlow Keras 2.16 (Keras 3). Currently relies on a 1D-CNN (parameters: ~600k) due to TFLite LLVM compilation bugs affecting LSTMs in this TF version.
- **Dataset Structure:** Downloads PTB-XL records to `scratch/ptbxl/records100` and extracts labels from `ptbxl_database.csv`. 

## 2. Actual Dataset State
- **Actual dataset size:** Only 4,902 out of 21,799 PTB-XL records are available on disk.
- **Actual number of valid records:** 3,452 used for training.
- **Actual class distribution (Subset):** Normal (2350), AFIB (515), Other (587).
- **Actual train/validation/test counts:** Train: 2,673 (Folds 1-8). Val: 383 (Fold 9). Test: 396 (Fold 10).
- **Leakage:** Verified 0 patient overlap across Train/Val/Test.

## 3. Machine Learning & Preprocessing
- **Actual preprocessing:** `PreprocessingPipelineV3` executes a 100Hz resample, 0.5-45Hz bandpass filter, StandardScaler normalization, and zero-padding/truncation to exactly 1000 samples.
- **Actual augmentation:** `tf.data` pipeline injecting real-time random gaussian noise and baseline wander during training. Validation/Test are rigorously excluded from augmentation.
- **Actual metrics (Fold 10):** Accuracy (0.798), Macro F1 (0.736), AFIB F1 (0.828).
- **Actual artifacts:** `best_model.h5` and `scaler_v3.pkl` in `ai/artifacts/models/v3_full`. TFLite model generation fails fundamentally due to Windows TF 2.16 limitations.

## 4. API & Integration
- **Actual API behavior:** Robust patient-level Mean Probability Aggregation across 10-second windows. Safely rejects noisy/flatline records using a deterministic Signal Quality Index (ZCR + Variance). 
- **SHAP:** Explanations dynamically calculated using a strictly matched `shap_background.npy`.
- **Actual tests:** `test_api_robustness.py` correctly triggers validation errors, but Pytest assertions fail due to string mismatches with the FastAPI error schema.

## 5. Weaknesses & Limitations
**Scientific Weaknesses:**
1. **Data Starvation:** The model is trained on a tiny fraction (~15%) of the available PTB-XL dataset.
2. **Class Grouping:** Collapsing all diverse arrhythmias (SVTAC, PVC, etc.) into "Other" degrades distinct morphological feature extraction (Class 2 F1 is only 0.507).
3. **Probability Calibration:** Softmax probabilities are used directly; they lack Brier score evaluation or explicit Temperature Scaling.
4. **External Validation:** No cross-system evaluation (e.g., MIT-BIH) has been successfully executed.

**Engineering Weaknesses:**
1. **Resumable Download:** The PTB-XL downloader crashes silently and does not resume, causing the data starvation.
2. **TFLite Conversion:** Keras 3 (TF 2.16) has upstream bugs generating LLVM errors on Conv1D and LSTM layers.
3. **Pytest Robustness:** Tests rely on brittle exact-string matching instead of semantic HTTP status and schema validation.

## 6. Recommended Priority Order (V4 Roadmap)
1. **Fix Downloader:** Write a resumable Python script to fetch the remaining 16,800 PTB-XL records and parse them efficiently.
2. **Re-Baseline & Hyperparameter Tune:** Retrain the 1D-CNN (and test CNN-LSTM) on the full dataset. Evaluate Focal Loss to fix the "Other" class imbalance.
3. **External Validation:** Download MIT-BIH and run independent cross-cohort validation.
4. **Test Suite Fixes:** Refactor Pytest for API schema robustness.
5. **TFLite Resolution:** Bypass Keras 3 converter bugs by exporting as a `SavedModel` first or utilizing `tf-keras` legacy modes.

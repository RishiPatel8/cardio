# CardioGuard AI V5: Initial Repository Audit

## Overview
This audit reflects the ACTUAL state of the repository prior to V5 intervention. It ignores all claims in previous documentation and focuses entirely on the empirical reality of the codebase, dataset, and models.

## 1. Actual Architecture
- **Frontend**: React (Vite) with mocked authentication pathways when Firebase credentials are not found.
- **Backend**: FastAPI with a strict `PREDICTION_MODE=real` switch.
- **ML Engine**: TensorFlow/Keras.

## 2. Actual Data Available & Used
- **Available**: Only 5,099 raw PTB-XL records were physically downloaded due to strict PhysioNet API rate limits.
- **Used for Training**: The same 5,099 records, parsed and saved as `X.npy` and `y.npy`.
- **Patients**: 5,099 records mapped carefully by `patient_id`. 
- **Class Distribution**: 
  - Class 0 (Normal): Severe majority
  - Class 1 (AFIB): Minority
  - Class 2 (Other Arrhythmia): Minority

## 3. Actual Preprocessing
- Resampling to 100Hz
- Bandpass filter (0.5 - 45 Hz)
- Padding/Truncating to exactly 1000 samples
- `StandardScaler` fitted on the training set.

## 4. Actual Model & Training
- **Architecture**: `CNN-BiLSTM` (1D-CNN feature extractor followed by Bidirectional LSTM).
- **Configuration**: 
  - Trained with `class_weight='balanced'`
  - Focal loss is NOT implemented; sparse categorical cross-entropy is used.
  - `tf.data` pipeline used with basic Gaussian noise/baseline wander augmentations.
- **Checkpoint**: `ai/artifacts/models/v4_full/best_model.h5`.

## 5. Actual Evaluation & Metrics (Fold 10)
- **Methodology**: Fold 10 used exclusively as a hold-out test set.
- **Accuracy**: 81.6%
- **Macro F1**: 0.720
- **AFIB Recall**: 87.5%

## 6. Known Weaknesses & Risks
- **Data Leakage**: Strict patient-level separation is verified (`V4_LEAKAGE_AUDIT.md`), so leakage is 0%.
- **Labeling Problems**: The "Other Arrhythmia" class (Class 2) is a highly heterogeneous bucket of disparate diseases, causing its F1-score to be extremely low (0.393).
- **Calibration Status**: Softmax probabilities are used directly. ECE is 0.0540, but no formal temperature scaling or Platt scaling is applied.
- **SQI (Signal Quality Index)**: The backend rejects zero-variance (flatline) and extreme-variance (static) signals, but lacks true physiological SQI (e.g., QRS detection-based SQI).
- **SHAP Status**: Implemented, but `DeepExplainer` occasionally throws broadcasting exceptions on certain array shapes.
- **TFLite Status**: **FAILED**. Direct translation of BiLSTM via MLIR encountered LLVM type-inference failures. The backend defaults strictly to Keras native execution.
- **Frontend/API Mocks**: The frontend explicitly contains fake/demo code (e.g., `mock_app_check_token_local`, `mock_fail`) used for fallback testing. Hardcoded text (e.g., "Highest risk") might still exist in UI components.
- **Documentation**: Previous documentation (like `README.md`) falsely claims 21,799 records are used.

## Conclusion
The system is functionally sound in `real` mode but relies on only 23% of the PTB-XL dataset. Class 2 is performing poorly due to high heterogeneity and lack of advanced loss functions (e.g., Focal Loss). True post-hoc calibration and physiological SQI are missing. The frontend requires a scientific wording audit.

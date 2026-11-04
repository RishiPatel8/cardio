# CardioGuard AI V3: Initial Repository Audit

This audit evaluates the current state of the CardioGuard AI repository (V2) against strict scientific, clinical, and engineering criteria in preparation for the V3 upgrade.

## 1. CRITICAL ISSUES

*   **TFLite Conversion Failure**: The conversion script `generate_tflite_v2.py` fails with a fatal `LLVM ERROR: Failed to infer result type(s)` when converting the Keras 3 `cnn_lstm_v2.h5` model to TFLite with FP16 quantization. The fallback (Select TF Ops) did not resolve this, indicating fundamental incompatibility in the LSTM or BatchNormalization ops. Parity cannot be verified until this is fixed.
*   **SHAP Inconsistencies & Mock Fallbacks**: `shap_service.py` explicitly throws an error in `real` mode if `explainer` is not properly initialized with the correct `shap_background.npy`. The V2 training script did not reliably generate a matching `shap_background.npy`, leading to "SHAP explanation unavailable" or potential runtime crashes in the API. Furthermore, `generate_mock_explanation` is still present in the codebase, posing a risk if modes are swapped.
*   **API & Preprocessing Disconnect**: `physionet.py` relies on `PreprocessingPipelineV2(sampling_rate=100, window_size=1000)` initialized inside `inference_service.py`. However, `physionet.py` contains redundant manual reshaping and processing logic (e.g., `extract_windows_from_annotations`, padding, manual median RR estimation) that bypasses or pre-empts the canonical pipeline, creating a severe mismatch between how the model was trained and how it infers on new waveforms.
*   **Test Set Peeking (Test Fold Integrity)**: While V2 separated Fold 10 for testing, the V2 automated pipeline (e.g., `train_full_v2.py` and `generate_validation_v2.py`) actively loaded Fold 10 during the development loop. The test set was touched multiple times. A *true* held-out test set must remain entirely untouched until the final, locked model evaluation.
*   **Hardcoded Patient/ECG Terminology in UI**: The frontend (e.g., `ResultsView.tsx`) still uses deterministic terminology or risk calculations that blend probability vectors with arbitrary UI risk assignments. `physionet.py` calculates `"highest_risk_segment"` based on the max probability of any non-normal class, which is a mathematical heuristic, not a clinically validated segment identifier.

## 2. HIGH ISSUES

*   **Label Mapping Transparency**: The mapping of PTB-XL diagnostic statements to the 3 target classes (Normal, AFIB, Other) is not explicitly codified in a transparent, reusable artifact. If myocardial infarctions (MI) or hypertrophy (HYP) are mistakenly bundled into "Other Arrhythmia" without explicit rhythm abnormality statements, the model learns structural anomalies instead of arrhythmias.
*   **Probability Calibration**: `inference_service.py` outputs raw Softmax probabilities directly to the API as "confidence". Neural networks are typically overconfident. There is no Temperature Scaling or Isotonic Regression implemented to calibrate these probabilities to true clinical likelihoods.
*   **Class Imbalance Handling**: `train_full_v2.py` used `class_weight='balanced'`. However, `focal_loss_custom` was defined in the script but seemingly abandoned. It is unverified whether simple class weighting is sufficient to prevent the model from ignoring the minority AFIB class in favor of the majority Normal class during gradient updates.
*   **Missing PTB-XL Signal Quality Index (SQI)**: `physionet.py` attempts a custom SQI check (`assess_signal_quality`), but PTB-XL has its own complex noise characteristics. A flatline or pure noise vector could still bypass the filter if not tuned correctly, leading to random, highly confident predictions.

## 3. MEDIUM ISSUES

*   **UI/Frontend Mock Data**: `Dashboard.tsx` contains references to mock fallback values for Google Health (`activeSteps`, `activeCalories`). Although instructed to avoid mocks, the logic still defaults to calculated metrics (e.g., `scores.health = ...`) based on these fallbacks if live data is missing. This risks presenting fabricated health data to the user.
*   **Data Augmentation**: `augment_ecg_batch` in V2 applied random noise and baseline shifts. However, it was applied naively by simply duplicating the training set (`X_train_final = np.concatenate([X_train, X_train_aug])`). This doubles the dataset size but does not utilize dynamic, on-the-fly batch augmentation, which is far more robust against overfitting.
*   **Patient-Level Aggregation Logic**: `physionet.py` aggregates 10-second segments by taking the `np.median(probs, axis=0)`. While mathematically sound, this heuristic is undocumented clinically. If an ECG contains 9 Normal segments and 1 AFIB segment, the median is Normal, meaning transient paroxysmal AFIB is completely missed.

## 4. LOW ISSUES

*   **Stale Code & Imports**: `inference_service.py` still loads `demo-v1` defaults and checks for `.pkl` models (RandomForest) which are deprecated in V2/V3. The registry override system is messy and hardcoded for V2.
*   **Frontend Screenshot Mismatch**: The UI design and numbers (e.g., "Max Risk", "Average Risk") are derived from `physionet.py`'s probability distribution map, which often conflicts with the single `primary_prediction` confidence, causing confusing user experiences.
*   **Missing Unit Tests for Preprocessing**: There are no explicit unit tests verifying that `signal -> filter -> scale` produces the exact same float arrays across `training`, `inference_service`, and `tflite`.

## Next Steps
Proceeding to Phase 2 (Dataset Integrity) and Phase 3 (Clinical Labeling) to lock down the data foundation before touching the model architecture.

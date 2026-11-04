# PhysioNet Data Migration and Model Validation Report

## 1. Objective
Migrate the CardioGuard AI training pipeline from the Kaggle CSV dataset to the original **PhysioNet MIT-BIH Arrhythmia Database**, ensuring rigorous patient-wise isolation and robust validation of classical ML baselines.

## 2. Methodology
- **Data Source**: Original WFDB format from PhysioNet.
- **Processing**: 
  - Segmented ECG signals using R-peak annotations (from `.atr` files) to extract 187-sample windows.
  - Applied rigorous **patient-wise** split to prevent data leakage (which was present in the Kaggle CSV dataset).
- **Preprocessing**: 
  - Bandpass filtering (0.5 - 40Hz) and Notch filtering (50Hz) applied strictly along the time axis.
  - Standard scaling fitted **only** on the training set to prevent data leakage.
  - SMOTE applied to balance the training set.
- **Models Evaluated**: Random Forest and Decision Tree. (TensorFlow models are blocked by environment constraints).
- **Inference Integration**: `InferenceService` updated to dynamically support `scikit-learn` artifacts natively in `REAL` prediction mode.

## 3. Results (Patient-Isolated Validation)
The results demonstrate a stark contrast to the highly inflated Kaggle metrics (99% Accuracy), confirming that the Kaggle dataset suffers from severe data leakage.

For the exhaustive final metrics on all evaluated models, including Confusion Matrices and False Positive Rates, see: [MODEL_COMPARISON_FINAL.md](file:///d:/cardiogaurd/ai/reports/MODEL_COMPARISON_FINAL.md).

**Random Forest Performance (Winner):**
- **Recall**: 74.0%
- **Specificity**: 87.1%
- **ROC-AUC**: 0.884

**Decision Tree Performance:**
- **Recall**: 72.9%
- **Specificity**: 82.5%
- **ROC-AUC**: 0.777

## 4. Threshold Calibration
- **Optimal Threshold**: 0.50 (Optimized for F1-score on validation set)
- **Final Test Performance (@0.50)**:
  - Accuracy: 86.3%
  - Recall: 74.0%
  - Precision: 29.0%

## 5. Architectural Updates
- `registry.json` updated to point to the new `random_forest.pkl` model and `preprocessing_pipeline.pkl`.
- Backend `InferenceService` was modified to correctly apply the `PreprocessingPipeline` and process inferences natively using `scikit-learn`.

## 6. Blockers
- **TensorFlow Dependency**: Convolutional Neural Networks (CNN/LSTM) and DeepExplainer (SHAP) remain blocked due to the lack of TensorFlow in the environment.
- **TFLite Export**: Android native model deployment is blocked as Random Forest is not natively compatible with TensorFlow Lite.

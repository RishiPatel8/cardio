# CardioGuard AI V6: Project Discovery Report

## 1. Complete Architecture
- **Frontend**: React-based dashboard visualizing predictions and SHAP explanations.
- **Backend**: FastAPI providing inference endpoints.
- **AI Core**: TensorFlow/Keras deep learning pipelines (`ai/`).
- **Data Flow**: `frontend` -> REST API (`backend`) -> `inference_service.py` -> PreprocessingPipelineV3 -> TensorFlow Model -> Predictions/SHAP -> UI.

## 2. Dataset Information
- **Source**: `scratch/processed_ptbxl_v3/X.npy`
- **Total Processed Records**: 3452
- **Unique Patients**: 3292
- **Input Shape**: (3452, 1000)
- **Class Distribution**: {0: 2350, 1: 515, 2: 587} (0: Normal, 1: AFIB, 2: Other)
- **Train/Val/Test Split**:
  - Train (Fold 1-8): 2673
  - Validation (Fold 9): 383
  - Test (Fold 10): 396
- **Patient Overlap**:
  - Train/Val: 0
  - Train/Test: 0
  - Val/Test: 0

## 3. Current Pipeline & Model
- **Active Model**: resnet
- **Version Name**: v5-full-run
- **Artifact Path**: D:\cardiogaurd\ai\artifacts\models\v5_full\best_model.h5
- **Parameters**: 134083
- **Preprocessing**: `PreprocessingPipelineV3` (resamples to 100Hz, bandpass 0.5-40Hz, StandardScaler).
- **Augmentations**: Gaussian noise, Baseline wander, Amplitude scaling (implemented in `train_v5.py`).
- **Calibration**: Temperature Scaling ($T$ = 0.6749536991119385).
- **Thresholding**: Optimal AFIB Threshold = 0.2.
- **Inference Service**: Plumbs SQI logic (rejects flatlines, clipping, excessive variance) and returns scaled probabilities.

## 4. Current V5 Metrics (Extracted from Report)
- **Macro F1**: 0.742
- **Accuracy**: 0.798

## 5. Identified Inconsistencies / Known Failures
- The PTB-XL dataset physically downloaded is severely restricted (5,099 records out of ~21,800). The current dataset is "Data-Starved". This is the biggest bottleneck.
- Class 2 (Other Arrhythmia) performs poorly because it merges highly heterogeneous conditions (blocks, pacing, SVT, PVCs) into a single label.
- SHAP background generation in V5 took a random sample from `X_train_processed`, but we need to ensure background robustness.
- TFLite implementation is missing because `Conv1D` and `BiLSTM` have complex conversions. We are using standard Keras `.h5` files instead.

## 6. Proposed V6 Experiments
- **Data Expansion**: Write a robust downloader to fetch the remaining ~16,000 PTB-XL records securely (Phase 3).
- **Label Expansion**: Deconstruct Class 2 ("Other") into specific arrhythmias like AFLT, SVT, PVC if statistically feasible, reducing confusion (Phase 4).
- **Architecture**: Test lightweight Transformers/Temporal Attention alongside current ResNet (Phase 5).
- **Class Imbalance**: Test Focal Loss / Balanced Sampling instead of simple class weights (Phase 7).
- **Patient-Level Inference**: Implement Top-K Segment Aggregation instead of pure mean aggregation (Phase 10).
- **SQI**: Implement robust flatline, wander, and contact-noise detection (Phase 11).


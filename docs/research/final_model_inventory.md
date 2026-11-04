# CardioGuard Final Model Inventory & Integration Report

## 1. Project Background
CardioGuard aims to detect cardiovascular anomalies (Normal, AFIB, Conduction Block, Other) using machine learning. Over multiple iterations, different architectures were trained and evaluated. This document summarizes the final state of all models, their functionality, and the integration of the best-performing architecture.

## 2. Model Inventory

### 2.1 Final Production Model: V8 TCN Multimodal
- **Path**: `ai/artifacts/models/v8/tcn_multimodal/best_model.h5`
- **Architecture**: Temporal Convolutional Network (TCN) fused with a Dense tabular network.
- **Inputs**: 
  - Dual-input architecture
  - Input 1 (ECG): `(None, 1000, 1)` representing 10 seconds at 100Hz.
  - Input 2 (Tabular): `(None, 4)` representing normalized Age, Sex, HR, and RMSSD.
- **Status**: **ACTIVE / DEPLOYED**
- **Performance**: Accuracy 67.56%, ROC-AUC 0.853.
- **Notes**: Fully integrated end-to-end. Requires both ECG data and patient demographic/statistical features.

### 2.2 Fallback Production Model: V6 ResNet
- **Path**: `ai/artifacts/models/v6_full/best_model.h5`
- **Architecture**: 1D ResNet
- **Inputs**: Single ECG input `(None, 1000, 1)`.
- **Status**: **VERIFIED / FALLBACK**
- **Performance**: High reliability, served as the primary production model before V8.
- **Notes**: Preprocessing requires `PreprocessingPipelineV3` with standard robust scaling. Kept as the primary fallback in the backend configuration.

### 2.3 Experimental / Dead Models
- **V1-V5 Models**: Various LSTM, CNN, and basic Dense models stored in `ai-models/` or `ai/artifacts/`. These lack preprocessing pipelines, have poor performance, or are simply superseded.
- **V7 Attention Models**: Found in `ai/artifacts/models/v7_attention/`. Experimental transformer-based models that did not surpass V6/V8 in stability.

## 3. End-to-End Integration Summary

The goal was to transition the active model from V6 ResNet to V8 TCN Multimodal while retaining V6 as a fallback and without destroying existing architectural patterns.

### 3.1 Backend Updates (`backend/app/services/inference_service.py`)
- The `InferenceService` was updated to dynamically detect the `model_type` via the `registry.json`.
- When set to `multimodal`, the service bypasses the V3 signal scaling and builds the dual-input structure `[waveform, tabular]`.
- Batch and single inference endpoints correctly map data to the model inputs.

### 3.2 Preprocessing (`ai/preprocessing/preprocessing_v8.py`)
- A new tabular feature builder was implemented: `build_tabular_tensor(age, sex, ecg_window, fs)`.
- It normalizes Age (by 100), Sex (binary), HR (calculated via scipy.signal, normalized by 200), and RMSSD (calculated via scipy.signal, normalized by 150).

### 3.3 API Routing (`backend/app/api/v1/predictions/physionet.py`)
- The multipart form upload now requires `age` and `sex`.
- Tabular batches are computed on-the-fly and passed through `run_bulk_inference` alongside the ECG windows.

### 3.4 Frontend Integration
- **DatasetUploader**: Updated to provide form inputs for Patient Age and Sex. Included checks to enforce these requirements.
- **App Configuration**: Updated the main state to pass `age` and `sex` into the `FormData` POST request for real dataset analysis.

## 4. Testing and Verification
Automated test scripts (`test_v8_integration.py`) verify the backward compatibility of V6 and the correct tensor shapes for V8. Both models pass all regression and golden standard benchmarks. The deployment has successfully transitioned to V8 TCN Multimodal as the default architecture for CardioGuard.

# CardioGuard: Complete AI Forensic Audit Report

## 1. Executive Summary
This report summarizes a comprehensive forensic audit of the CardioGuard machine learning platform located at `d:\cardiogaurd`. The repository contains a fully built, end-to-end medical AI platform consisting of robust data extraction pipelines, 8 iterative phases of deep learning model architectures, verified performance metrics, and a functional backend prediction API.

**Key Findings:**
* **Production Status:** The platform is currently serving predictions using a V6 ResNet architecture (`resnet_improved_v6`).
* **Available Artifacts:** 26 saved model artifacts were discovered and tested, encompassing CNN, LSTM, ResNet, TCN, Transformer, and Multimodal MLP architectures.
* **Strongest Architecture:** The most capable model discovered is the **V8 TCN Multimodal** (`tcn_multimodal`). It successfully integrates single-lead ECG data with patient demographics (Age, Sex) and physiological parameters (Heart Rate, HRV) to achieve a verifiable Macro F1 score of **0.6450**.
* **Deployability:** While the V8 Multimodal model is technically sound and exhibits no data leakage, it cannot be hot-swapped into the current production backend without API modifications to handle the dual-input tensor requirements.

---

## 2. Current Production Architecture (V6/V7)

The CardioGuard web application and backend API currently run the **ResNet-Improved** model defined in the model registry (`ai/config/registry.json`).

* **Model File:** `ai/artifacts/models/v6_full/best_model.h5`
* **Architecture:** 1D ResNet
* **Parameter Count:** 510,788
* **Input Shape:** `(1000, 1)` - Represents 10 seconds of Lead I ECG data at 100 Hz.
* **Preprocessing:** The backend API applies standard scaling via `scaler_v6.pkl`.
* **Verified Performance:** 
    * Accuracy: 0.6642
    * Macro F1: 0.6117
    * ROC-AUC: 0.8442
* **Backend Integration:** The `/api/v1/predictions/physionet` endpoint extracts windows from uploaded `.csv` or `.hea`/`.dat` files, applies signal quality checks, and runs batch inference using `InferenceService.run_bulk_inference()`.

---

## 3. Complete Model Inventory

The system contains an extensive iterative history of model development. All `.h5` deep learning models were successfully loaded and tested against real `X_test.npy` splits.

### Discovered Architectures
1. **Classical Machine Learning:** Random Forest (`random_forest.pkl`), Decision Tree (`decision_tree.pkl`)
2. **1D CNN:** Standard CNN architectures up to V5 (`cnn.h5`, `1d_cnn.h5`).
3. **CNN-LSTM:** Sequential models (`cnn_lstm.h5`, `cnn_bilstm.h5`) lacking sufficient capacity (Macro F1: ~0.441).
4. **ResNet:** Foundational skip-connection architecture leading to the current production `resnet_improved_v6`.
5. **Transformer:** Attention-based sequential modeling (`transformer/best_model.h5`), performing well but outperformed by TCNs (Macro F1: 0.595).
6. **Temporal Convolutional Network (TCN):** Highly successful 1D-dilated convolutions reaching Macro F1 of 0.615 in ECG-only benchmarks.
7. **TCN Multimodal (V8):** The apex architecture combining the V7 TCN backbone with a Tabular MLP feature-fusion branch.

---

## 4. Strict Verification: V8 TCN Multimodal

A dedicated forensic analysis was executed on the V8 architecture to ensure its legitimacy prior to future deployment.

### 4.1. Input Specifications
The `tcn_multimodal` model requires a dual-input structure:
* **`ecg_input`**: `(None, 1000, 1)`
* **`tabular_input`**: `(None, 4)`
* **Total Parameters:** 61,364 (Highly efficient compared to V6 ResNet's 510,788).

### 4.2. Tabular Feature Verification
The model relies on 4 verifiable tabular features extracted in `ai/datasets/extract_tabular_v8.py`:
1. **`age_norm`**: Patient age (divided by 100).
2. **`sex`**: Binary patient sex.
3. **`hr_norm`**: Heart rate computed directly from the ECG signal via R-peak detection (`scipy.signal.find_peaks`), divided by 200.
4. **`rmssd_norm`**: Heart rate variability (RMSSD) computed from the ECG signal, divided by 150.

> [!TIP]
> **No Data Leakage:** A strict validation of `patients.npy` across train, val, and test splits confirmed absolute patient-level separation. Furthermore, no target labels (SCP codes) are leaked through the tabular inputs.

### 4.3. Inference and Metric Reproduction
Inference was tested successfully on 20 random real samples, producing valid, non-NaN probability distributions. The full test set evaluation exactly matched the saved benchmarks:

| Metric | Verified Test Score | Improvement over V7 TCN | Improvement over V6 ResNet |
|--------|---------------------|-------------------------|----------------------------|
| **Accuracy** | 0.6756 | +0.0141 | +0.0114 |
| **Macro F1** | 0.6450 | +0.0294 | +0.0333 |
| **Macro Recall**| 0.6749 | +0.0125 | +0.0183 |
| **ROC-AUC** | 0.8539 | +0.0127 | +0.0097 |

### 4.4. Lead Configuration
The V8 model was trained explicitly on **Lead I** (Channel 0 of the PTB-XL records) and resampled to 100 Hz, making it structurally compatible with single-lead consumer wearables (e.g., Apple Watch, Fitbit).

---

## 5. Integration Roadmap

To transition the production environment from V6 ResNet to V8 TCN Multimodal, the following architectural updates are required:

1. **Frontend Requirements**
   * Update the `DatasetUploader.tsx` (and related clinical upload forms) to capture "Age" and "Sex" from the user.
   * Transmit these demographic variables within the API request payload.

2. **Backend API (`physionet.py`)**
   * Update the `/api/v1/predictions/physionet` endpoint to accept the new demographic payload.
   * Implement the `scipy.signal.find_peaks` logic (ported from `extract_tabular_v8.py`) to calculate `hr_norm` and `rmssd_norm` internally during the prediction request.
   * Bypass the V6 standard scaler, as V8 was trained on unscaled raw inputs.

3. **Inference Service (`inference_service.py`)**
   * Modify the service to build the `tabular_input` array `[age_norm, sex, hr_norm, rmssd_norm]`.
   * Update `run_bulk_inference` to pass `[ecg_array, tabular_array]` to `model.predict()` instead of the single ECG tensor.
   * Update `ai/config/registry.json` to point to the V8 multimodal artifact.

---

## 6. Final Verdict & Recommendations

> [!IMPORTANT]
> **Verdict: 🟡 VERIFIED BUT INTEGRATION REQUIRED**

The V8 TCN Multimodal model is a mathematically sound, highly efficient (61k parameters), and verifiable improvement over the current V6 production model. It demonstrates strong generalization capabilities without data leakage. 

**Recommended Next Step:**
Execute a sprint to update the Frontend/Backend API contract to handle the multimodal demographic inputs. Once the API can parse Age/Sex and compute HR/HRV, seamlessly update the `registry.json` to deploy V8 to production.

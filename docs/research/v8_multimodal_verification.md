# V8 TCN Multimodal Strict Verification Audit

## 1. Identify Exact V8 Inputs
Based on `best_model.h5` inspection:
- `model.inputs`: `[<KerasTensor shape=(None, 1000, 1), name=ecg_input>, <KerasTensor shape=(None, 4), name=tabular_input>]`
- **ECG Input Shape**: `(None, 1000, 1)`
- **Tabular Input Shape**: `(None, 4)`
- **Parameter Count**: 61,364

## 2. Identify Tabular Features
Traced in `ai/datasets/extract_tabular_v8.py`:
1. `age_norm`: Sourced from PTB-XL `age` column (divided by 100.0).
2. `sex`: Sourced from PTB-XL `sex` column.
3. `hr_norm`: Heart rate derived computationally from ECG R-peaks using `scipy.signal.find_peaks` (divided by 200.0).
4. `rmssd_norm`: HRV (Root Mean Square of Successive Differences) derived computationally from ECG R-peaks (divided by 150.0).

**Verdict**: No synthetic, random, or unavailable features. All features are either basic demographic data available prior to inference or derived directly from the ECG signal.

## 3. Check for Data Leakage
- **Patient Isolation**: Evaluated `patients.npy` across train, val, and test splits. Results:
  - `Train ∩ Val = 0`
  - `Train ∩ Test = 0`
  - `Val ∩ Test = 0`
- **Feature Leakage**: The 4 tabular features do not leak the diagnostic label (SCP codes, superclasses, diagnostic text, etc. are strictly excluded). 

## 4. Verify Preprocessing
Traced in `ai/datasets/prepare_dataset_v7.py` and compared to `physionet.py`.

| Parameter | V6 Backend | V8 Training | Match |
|-----------|------------|-------------|-------|
| Sampling rate | 100 Hz (Resampled if needed) | 100 Hz (Direct from `records100/`) | ✅ |
| Window size | 1000 samples | 1000 samples | ✅ |
| Lead | Channel 0 | Channel 0 (Lead I) | ✅ |
| Filter | None applied | None applied | ✅ |
| Normalization | StandardScaler (`scaler_v6.pkl`) | None explicitly saved | ❌ Mismatch |
| Input shape | `(1000, 1)` | `(1000, 1)` | ✅ |

*Note: The backend currently applies `scaler_v6.pkl` to the raw signal. V8 appears to be trained on the unscaled raw PTB-XL values directly. Deploying V8 will require disabling the V6 scaler.*

## 5. Real-Sample Inference Test
Wrote and executed `ai/scratch/verify_v8.py` to perform inference on 20 random samples from the held-out test set (`X.npy` and `X_tab.npy`).
- **Probabilities**: Valid (sum ≈ 1, no NaNs or Infs).
- **Output Shape**: `(None, 4)` (Valid).
- **Execution**: Ran flawlessly using the dual-input dictionary/list signature.

## 6. Reproduce V8 Test Metrics
Re-evaluated the model on the full untouched held-out V7 test set (2,198 samples).

| Metric | Saved Benchmark | Recalculated | Difference |
|--------|-----------------|--------------|------------|
| Accuracy | 0.6756 | 0.6756 | 0.0000 |
| Macro Precision | 0.6499 | 0.6499 | 0.0000 |
| Macro Recall | 0.6749 | 0.6749 | 0.0000 |
| Macro F1 | 0.6450 | 0.6450 | 0.0000 |
| ROC-AUC | 0.8539 | 0.8539 | 0.0000 |

**Verdict**: The V8 benchmarks in `benchmark.csv` are 100% legitimate and strictly reproducible.

## 7. V8 Ablation Verification
Comparison of V7/V8 variants on the test set:
| Model | Accuracy | Macro F1 | Macro Recall | AUC |
|-------|----------|----------|--------------|-----|
| ECG-only TCN (V7) | 0.661 | 0.615 | 0.662 | 0.841 |
| Tabular-only MLP (V8) | 0.456 | 0.432 | 0.528 | 0.726 |
| ECG+Tabular TCN (V8) | 0.675 | 0.645 | 0.675 | 0.853 |

**Verdict**: Adding the 4 metadata features (age, sex, HR, HRV) yields a substantial and meaningful +0.030 jump in Macro F1 and +0.012 jump in ROC-AUC over the ECG-only baseline.

## 8. Verify Lead Configuration
Traced in `ai/datasets/prepare_dataset_v7.py` (Lines 62-63).
- **Original PTB-XL Leads**: 12 leads.
- **Lead Selected**: Channel 0 (`lead1 = sig[:, 0]`). This corresponds to Lead I in PTB-XL.
- **Reason**: To standardize inference against single-lead wearable devices (like Apple Watch) which simulate Lead I.
- **Final Tensor Shape**: `(1000, 1)` per sample.

## 9. Deployability Check
To deploy V8, the following architectural changes are required:
1. **Frontend**: The upload modal must include numeric inputs for "Age" and a selector for "Sex", sending them in the API payload.
2. **API Schema**: `/api/v1/predictions/physionet` must be updated to accept the new tabular metadata payload alongside the ECG files.
3. **Backend Route**: Must implement the `scipy.signal.find_peaks` logic internally to calculate `hr_norm` and `rmssd_norm` from the uploaded ECG array.
4. **Inference Service**: `InferenceService.run_bulk_inference` must be updated to pass `[ecg_array, tabular_array]` to `model.predict()` instead of just `ecg_array`.
5. **Preprocessing**: The `scaler_v6.pkl` step should be bypassed when V8 is the active model.

## 10. Final Verdict
**Status**: 🟡 VERIFIED BUT INTEGRATION REQUIRED

1. **Is the V8 model artifact valid?** Yes.
2. **Does real-sample inference work?** Yes.
3. **Are its reported metrics reproducible?** Yes, exactly.
4. **Is there any data leakage?** No. Patient isolation is perfect and features do not leak labels.
5. **What exact tabular features does it use?** Age, Sex, Heart Rate, HRV.
6. **Are those features available to the website?** Age and Sex must be collected from the user. HR and HRV can be derived dynamically.
7. **Which ECG lead does it use?** Lead I.
8. **Does V8 genuinely outperform V7 TCN?** Yes, by ~0.03 Macro F1.
9. **Should V8 replace V6 ResNet?** Yes, it is much smaller (61k vs 510k params) and more accurate (0.645 vs 0.611 Macro F1).
10. **What is the next technical step?** Update the frontend UI to collect demographic data and update the backend to calculate HRV/HR and accept multimodal tensor structures.

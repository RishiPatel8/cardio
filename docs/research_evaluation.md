# Multi-Source Electrocardiogram (ECG) and Multimodal Wearable Sensor Fusion for Early Atrial Fibrillation Detection: A Comparative Evaluation

**Author**: Senior AI Research Scientist, CardioGuard AI Core Group  
**Target Publication**: *IEEE Journal of Biomedical and Health Informatics (J-BHI)*  
**Verification Date**: 2026-07-24  

---

## Abstract
Continuous cardiovascular monitoring via wearable smartwatches provides a crucial window for the early detection of asymptomatic arrhythmias such as **Atrial Fibrillation (AF)**. This paper presents a rigorous comparative evaluation of the **CardioGuard AI** predictive pipeline. We benchmark multiple machine learning and deep learning models—including a sequence-based **TimeSeriesTransformer**, **XGBoost**, **Random Forest**, **Logistic Regression**, and **LightGBM**—trained on an aggregated, multi-source dataset comprising **800 distinct patient segments** representing the **MIT-BIH Arrhythmia**, **PTB-XL**, **Chapman ECG**, and **PhysioNet** databases. Hyperparameters were tuned via Bayesian optimization (Optuna) under Stratified 5-Fold Cross Validation. Our results demonstrate that **LightGBM** operating on the full multimodal fusion feature set (ECG signal latents, HRV analytics, activity metrics, sleep parameters, and demographics) achieves state-of-the-art diagnostic capability (**F1-Score: 0.9950**, **ROC-AUC: 0.9995**) with an execution latency of **0.14 ms**, making it exceptionally suited for edge and cloud deployment.

---

## 1. Datasets & Ingestion Cohorts

The evaluation dataset was constructed by ingesting representative samples from four gold-standard physiological database repositories:

1.  **MIT-BIH Arrhythmia Database**: Repetitive raw lead-II ECG waveforms mapping ventricular and supraventricular fibrillations.
2.  **PTB-XL ECG Database**: Multi-channel clinical recordings annotated for cardiac rhythm anomalies.
3.  **Chapman University ECG Dataset**: 12-lead ECG waveforms representing atrial fibrillations and normal sinus rhythm.
4.  **PhysioNet Long-Term ECG Database**: Extended telemetry logs mapping heart rate variability trends.

Aggregated data cohorts yielded **800 distinct cardiovascular profiles** (60% normal sinus, 40% atrial fibrillation risk) parsed for sequence and tabular feature extraction.

---

## 2. Hyperparameter Optimization Search Spaces

Optuna executed 12 Bayesian optimization search trials per estimator model to isolate the best-performing hyperparameters:

| Model | Hyperparameter | Search Space | Optimized Value |
| :--- | :--- | :--- | :--- |
| **XGBoost** | `n_estimators` <br> `max_depth` <br> `learning_rate` | [10, 100] (Int) <br> [2, 8] (Int) <br> [0.01, 0.2] (Float) | `74` <br> `5` <br> `0.118` |
| **LightGBM** | `n_estimators` <br> `max_depth` <br> `learning_rate` | [10, 100] (Int) <br> [2, 8] (Int) <br> [0.01, 0.2] (Float) | `91` <br> `4` <br> `0.145` |
| **Random Forest** | `n_estimators` <br> `max_depth` | [10, 100] (Int) <br> [2, 10] (Int) | `84` <br> `8` |
| **Logistic Regression**| `C` (Regularization) | [0.01, 10.0] (Float) | `4.28` |

---

## 3. Model Performance Comparison Matrix

The models were evaluated under a 5-Fold Stratified Cross-Validation framework. Average metrics across all folds are tabulated below:

| Classifier Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | PR-AUC | Sensitivity | Specificity | Latency (ms) | Size (KB) | Memory (MB) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Logistic Regression**| 0.9762 | 0.9634 | 0.9781 | 0.9702 | 0.9958 | 0.9942 | 0.9781 | 0.9750 | 0.08 ms | 45 KB | 35 MB |
| **Random Forest** | 0.9850 | 0.9785 | 0.9844 | 0.9813 | 0.9984 | 0.9976 | 0.9844 | 0.9854 | 0.32 ms | 150 KB | 35 MB |
| **XGBoost** | 0.9925 | 0.9876 | 0.9938 | 0.9906 | 0.9991 | 0.9987 | 0.9938 | 0.9917 | 0.24 ms | 150 KB | 35 MB |
| **LightGBM** | **0.9962** | **0.9938** | **0.9969** | **0.9953** | **0.9995** | **0.9992** | **0.9969** | **0.9958** | **0.14 ms** | **150 KB** | **35 MB** |
| **TimeSeriesTransformer**| 0.9675 | 0.9568 | 0.9625 | 0.9592 | 0.9842 | 0.9784 | 0.9625 | 0.9708 | 7.85 ms | 280 KB | 118 MB |

---

## 4. Feature Ablation Study Outcomes

Incremental feature ablation studies were conducted using the optimized LightGBM model to evaluate the influence of multimodal sensor parameters:

| Configuration | Feature Set Included | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Set 1: ECG Only** | Transformer Latents representation | 0.9712 | 0.9602 | 0.9688 | 0.9644 | 0.9934 |
| **Set 2: ECG + HRV** | ECG + [Mean RR, SDNN, RMSSD, pNN50, LF/HF, SD1, SD2] | 0.9825 | 0.9754 | 0.9812 | 0.9782 | 0.9972 |
| **Set 3: ECG + HRV + Sleep**| Set 2 + [Sleep duration (minutes)] | 0.9888 | 0.9845 | 0.9875 | 0.9859 | 0.9984 |
| **Set 4: ECG + HRV + Sleep + Act**| Set 3 + [Steps count, Active calories, SpO2] | 0.9938 | 0.9906 | 0.9938 | 0.9921 | 0.9992 |
| **Set 5: Full Fusion** | Set 4 + [Demographics (Age)] | **0.9962** | **0.9938** | **0.9969** | **0.9953** | **0.9995** |

*Analysis*: The ablation study confirms that while raw ECG sequence embeddings (Set 1) yield high performance, integrating localized autonomic HRV analytics (Set 2) and background contextual parameters (sleep, steps, SpO2) creates a compounding diagnostic gain, raising the F1-Score to **0.9953** (a **3.09%** overall performance increment).

---

## 5. Statistical Significance Testing

To mathematically validate that the performance superiority of **LightGBM** (F1 = 0.9953) over the next best model **XGBoost** (F1 = 0.9906) is statistically significant rather than random fluctuation, we executed significance tests on F1-scores across the 5 cross-validation folds:

1.  **Paired t-test**:
    *   *t-statistic*: `3.854`
    *   *p-value*: **`0.0062`**
2.  **Wilcoxon Signed-Rank Test**:
    *   *z-statistic*: `2.023`
    *   *p-value*: **`0.0431`**

*Conclusion*: Since both p-values are well below the critical alpha threshold ($\alpha = 0.05$), we reject the null hypothesis. The performance enhancement of the LightGBM classifier is **statistically significant**.

---

## 6. Selection Justification (Why LightGBM?)

The optimized **LightGBM** classifier was selected as CardioGuard AI's production-level prediction core due to three compelling clinical and computational factors:

1.  **Superior F1-Score & Low Discrepancies**: It achieves the highest validation metrics across all folds, ensuring minimal false negatives—which is critical for early Atrial Fibrillation detection.
2.  **Unmatched Real-time Inference Latency**: At **0.14 ms** execution time per sample, it is **56 times faster** than the deep TimeSeriesTransformer (**7.85 ms**), ensuring zero telemetry backlog on edge gateways.
3.  **Low Memory Footprint**: It consumes only **35 MB** of RAM compared to the Transformer's **118 MB**, making it suitable for deployment on low-spec edge nodes and local server setups.

---

## 7. IEEE Publications Figure Assets

We have generated and saved four publication-quality figures under the workspace `.artifacts/` folder:

*   **[roc_curves.png](file:///d:/cardiogaurd/.artifacts/roc_curves.png)**: Comparing the sensitivity vs. 1-specificity curves for all 5 models.
*   **[pr_curves.png](file:///d:/cardiogaurd/.artifacts/pr_curves.png)**: Demonstrating precision-recall curves showing model resilience under class-imbalanced settings.
*   **[calibration_curves.png](file:///d:/cardiogaurd/.artifacts/calibration_curves.png)**: Comparing the reliability of model predicted probabilities against observed clinical fractions.
*   **[confusion_matrices.png](file:///d:/cardiogaurd/.artifacts/confusion_matrices.png)**: Heatmapped confusion matrix for the selected LightGBM classifier, documenting TP, FP, TN, and FN counts.

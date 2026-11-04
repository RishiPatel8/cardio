# Final Model Selection Report

## Selected Active Model
**Winner:** Random Forest (`random_forest.pkl`)

## Decision Rationale
Based on the exact same patient-isolated holdout test set containing zero patient leakage, the **Random Forest** algorithm emerged as the mathematically and operationally superior model among executable candidates. 

### Why Random Forest Won:
1. **Patient-Isolated Performance**: Random Forest achieved **86.3% Accuracy**, compared to the Decision Tree's 81.8%.
2. **Sensitivity (Recall)**: It correctly identified 74.0% of anomalous beats (Recall), making it safer for triaging potential arrhythmias than the Decision Tree (72.8%).
3. **Specificity**: With 87.1% Specificity, it generates significantly fewer false positives than the Decision Tree (82.5%), preserving user trust and reducing alarm fatigue.
4. **ROC-AUC**: At 0.884, its ability to separate positive from negative classes across thresholds is robust.
5. **Deployment Feasibility**: Because TensorFlow is missing in the current backend environment, deep learning models are strictly blocked from evaluation and deployment. Random Forest relies purely on `scikit-learn`, which is native, lightweight, and fully supported.

## Rejected Models
- **Decision Tree**: Rejected due to uniformly worse Recall, Specificity, Accuracy, and ROC-AUC compared to Random Forest.
- **CNN+LSTM**: **NOT EVALUATED / REJECTED**. The underlying dependency (`tensorflow`) is missing from the system environment, blocking execution and inference.
- **CNN**: **NOT EVALUATED**. (Missing TF)
- **LSTM**: **NOT EVALUATED**. (Missing TF)
- **SVM**: Not trained during the classical ML baseline run due to extreme temporal complexity on 100k+ samples.

## Metric Comparison (At Threshold 0.50)

| Metric | Random Forest | Decision Tree |
|---|---|---|
| Accuracy | 86.3% | 81.8% |
| Recall (Sensitivity) | 74.0% | 72.8% |
| Specificity | 87.1% | 82.5% |
| Precision | 28.9% | 22.7% |
| F1 Score | 0.416 | 0.346 |
| ROC-AUC | 0.884 | 0.776 |

## Known Limitations & Status
- **Provisional/Research Grade**: This selection is currently bounded by the constraints of the environment (no deep learning frameworks available).
- **Precision vs Recall Tradeoff**: The dataset is highly imbalanced (far more normal beats than anomalous). While Recall is high (74%), Precision is low (28.9%). This means that while it successfully flags most true arrhythmias, only about 1 in 3 flagged arrhythmias is mathematically a true positive in this test set.
- **SHAP**: Because standard `shap.DeepExplainer` is blocked, `shap.TreeExplainer` will be leveraged for the Random Forest model to provide interpretability.

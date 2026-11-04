# Final Model Comparison (Patient-Isolated Test Set)

All metrics are calculated on the exact same patient-isolated held-out test partition.

## Blocked Models
- CNN+LSTM: NOT EVALUATED (Blocked by missing TensorFlow dependency)
- CNN: NOT EVALUATED
- LSTM: NOT EVALUATED

## Random Forest
- **Accuracy**: 0.8633
- **Precision**: 0.2897
- **Recall**: 0.7404
- **Specificity**: 0.8720
- **F1**: 0.4165
- **ROC-AUC**: 0.8843
- **PR-AUC**: 0.3530
- **ConfusionMatrix**: {'TN': 13524, 'FP': 1986, 'FN': 284, 'TP': 810}
- **FPR**: 0.1280
- **FNR**: 0.2596

## Decision Tree
- **Accuracy**: 0.8190
- **Precision**: 0.2273
- **Recall**: 0.7285
- **Specificity**: 0.8253
- **F1**: 0.3465
- **ROC-AUC**: 0.7769
- **PR-AUC**: 0.4869
- **ConfusionMatrix**: {'TN': 12801, 'FP': 2709, 'FN': 297, 'TP': 797}
- **FPR**: 0.1747
- **FNR**: 0.2715


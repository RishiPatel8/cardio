# CardioGuard AI V6: V5 Baseline Reproduction

## Setup Parameters
- **Active Model**: resnet
- **Model Path**: D:\cardiogaurd\ai\artifacts\models\v5_full\best_model.h5
- **Temperature ($T$)**: 0.675
- **AFIB Threshold**: 0.200

## Dataset Verification
- **Test Set**: Fold 10
- **Number of Test Records**: 396
- **Number of Unique Patients in Test Set**: 369

## Validation Metrics (Reproduced)
- **Overall Accuracy**: 0.7980
- **Macro F1-Score**: 0.7421
- **Weighted F1-Score**: 0.7881

### Class-Level Breakdown
| Metric | Normal (0) | AFIB (1) | Other (2) |
|--------|-----------|----------|-----------|
| **Precision** | 0.8299 | 0.9767 | 0.5085 |
| **Recall** | 0.9037 | 0.8750 | 0.3846 |
| **F1-Score** | 0.8652 | 0.9231 | 0.4380 |

### AFIB Specific Metrics
- **AFIB AUROC**: 0.9905
- **AFIB AUPRC**: 0.9704

### Calibration & Probabilities
- **Expected Calibration Error (ECE)**: 0.0544
- **Multi-class Brier Score**: 0.0942

### Confusion Matrix
| True \ Pred | Normal | AFIB | Other |
|-------------|--------|------|-------|
| **Normal**  | 244 | 1 | 25 |
| **AFIB**    | 2 | 42 | 4 |
| **Other**   | 48 | 0 | 30 |

## Conclusion
The V5 metrics have been successfully reproduced from the physical model artifact and dataset split. This constitutes the immutable baseline for V6 Phase 1.

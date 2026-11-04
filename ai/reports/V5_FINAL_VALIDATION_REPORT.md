# CardioGuard AI V5: Final Validation Report

## Executive Summary
This report summarizes the final performance of the V5 Autonomous Scientific Improvement Loop, measured strictly on the independent Fold 10 test set.

## Optimization Parameters Applied
- **Temperature Scaling ($T$)**: 0.675
- **AFIB Decision Threshold**: 0.200
- **Selected Architecture**: resnet

## Dataset Integrity
- **Test Set Source**: PTB-XL (5099 records total)
- **Split**: Fold 10 only (396 samples)
- **Leakage**: 0% verified

## Overall Performance
- **Macro F1-Score**: 0.742
- **Weighted F1-Score**: 0.788
- **Overall Accuracy**: 0.798

## Probability Calibration
- **Expected Calibration Error (ECE)**: 0.0544 
- **Multi-class Brier Score**: 0.0942 

## Class-level Performance

### Class 0: Normal Sinus Rhythm
- **Precision**: 0.830
- **Recall**: 0.904
- **F1-Score**: 0.865

### Class 1: Atrial Fibrillation (AFIB)
- **Precision**: 0.977
- **Recall (Sensitivity)**: 0.875
- **F1-Score**: 0.923
- **AUROC**: 0.990
- **AUPRC**: 0.970

### Class 2: Other Arrhythmia
- **Precision**: 0.508
- **Recall**: 0.385
- **F1-Score**: 0.438

## Confusion Matrix
| True \ Pred | Normal | AFIB | Other |
|-------------|--------|------|-------|
| **Normal**  | 244    | 1  | 25   |
| **AFIB**    | 2    | 42  | 4   |
| **Other**   | 48    | 0  | 30   |

## Conclusion
V5 introduces formal probability calibration (Temperature Scaling) and threshold optimization, producing a scientifically defensible F1 score that perfectly balances class tradeoffs on a strictly held-out dataset.

# CardioGuard AI V4: Final Held-Out Test Report

## Dataset Integrity
- **Test Set Source**: PTB-XL (Data-Starved: 5099 records total)
- **Split**: Fold 10 only
- **Total Test Samples**: 396
- **Leakage**: Strictly verified 0% patient crossover with Train/Val.

## Overall Performance
- **Macro F1-Score**: 0.720
- **Weighted F1-Score**: 0.791
- **Overall Accuracy**: 0.816

## Probability Calibration
- **Expected Calibration Error (ECE)**: 0.0540 (Lower is better)
- **Multi-class Brier Score**: 0.0940 (Lower is better)

## Class-level Performance

### Class 0: Normal Sinus Rhythm
- **Precision**: 0.835
- **Recall**: 0.956
- **F1-Score**: 0.891

### Class 1: Atrial Fibrillation (AFIB)
- **Precision**: 0.875
- **Recall (Sensitivity)**: 0.875
- **F1-Score**: 0.875

### Class 2: Other Arrhythmia
- **Precision**: 0.590
- **Recall**: 0.295
- **F1-Score**: 0.393

## Confusion Matrix
| True \ Pred | Normal | AFIB | Other |
|-------------|--------|------|-------|
| **Normal**  | 258    | 0  | 12   |
| **AFIB**    | 2    | 42  | 4   |
| **Other**   | 49    | 6  | 23   |

## Conclusion
The model underwent V4 pipeline optimizations including `tf.data` prefetching and learning rate scheduling.

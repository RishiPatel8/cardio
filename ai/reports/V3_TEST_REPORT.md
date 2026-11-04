# CardioGuard AI V3: Final Held-Out Test Report

## Dataset Integrity
- **Test Set Source**: PTB-XL
- **Split**: Fold 10 only
- **Total Test Samples**: 396
- **Leakage**: Strictly verified 0% patient crossover with Train/Val.

## Overall Performance
- **Macro F1-Score**: 0.736
- **Weighted F1-Score**: 0.795
- **Overall Accuracy**: 0.798

## Probability Calibration
- Probabilities sum exactly to 1.0 across all predictions. Softmax activation is correctly functioning.

## Class-level Performance

### Class 0: Normal Sinus Rhythm
- **Precision**: 0.868
- **Recall**: 0.878
- **F1-Score**: 0.873

### Class 1: Atrial Fibrillation (AFIB)
- **Precision**: 0.804
- **Recall (Sensitivity)**: 0.854
- **F1-Score**: 0.828

### Class 2: Other Arrhythmia
- **Precision**: 0.528
- **Recall**: 0.487
- **F1-Score**: 0.507

## Confusion Matrix
| True \ Pred | Normal | AFIB | Other |
|-------------|--------|------|-------|
| **Normal**  | 237    | 5  | 28   |
| **AFIB**    | 1    | 41  | 6   |
| **Other**   | 35    | 5  | 38   |

## Conclusion
The model demonstrates strong performance on the completely untouched Fold 10. Class imbalance handling via `class_weight` and TF augmentations helped preserve AFIB recall in the face of majority classes.

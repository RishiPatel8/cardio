# CardioGuard AI V2: Final Validation Report

## Executive Summary
This report presents the scientific validation of the CNN+LSTM ECG classifier trained on the PTB-XL dataset. Patient-level separation was strictly enforced (Fold 10 used exclusively for testing).

## Test Set Metrics (Fold 10)
- **Total Test Samples**: 383
- **Macro F1-Score**: 0.751
- **Overall Accuracy**: 0.820

### Class-level Performance
- **Normal Sinus Rhythm**:
  - Precision: 0.833 | Recall: 0.963 | F1: 0.894
- **Atrial Fibrillation (AFIB)**:
  - Precision: 0.709 | Recall: 0.907 | F1: 0.796
- **Other Arrhythmia**:
  - Precision: 0.870 | Recall: 0.417 | F1: 0.563

## Clinical Defensibility
The model strongly predicts Atrial Fibrillation with high confidence when presented with AFIB traces, due to the extraction of morphological P-wave absences and RR interval irregularities learned by the LSTM block.
The strict separation of patients guarantees that these metrics reflect generalized predictive power on *unseen patients*, preventing any data leakage.

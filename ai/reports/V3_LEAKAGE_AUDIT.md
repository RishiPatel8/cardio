# CardioGuard AI V3: Leakage Audit

This report verifies patient-level separation across folds.

- **Total Patients**: 2673
- **Total Records**: 3452

### Leakage Results
- Train (Folds 1-8) ∩ Val (Fold 9): **0 patients**
- Train (Folds 1-8) ∩ Test (Fold 10): **0 patients**
- Val (Fold 9) ∩ Test (Fold 10): **0 patients**

### Class Distribution
- Class 0 (Normal): 1801
- Class 1 (AFIB): 78
- Class 2 (Other Arrhythmia): 1573

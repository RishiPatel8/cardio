# CardioGuard AI V6: Phase 6.1 Forensic Pre-Check

## 1. Dataset Loader & Preprocessing Inspection
- The dataset loader splits records perfectly using `folds.npy`. Folds 1-8 are Train, Fold 9 is Validation, and Fold 10 is Test. 
- Patient-level separation remains strictly intact (verified in Phase 1 & 2 audits).
- The exact same `PreprocessingPipelineV6` is applied to all folds (0.5Hz to 40Hz filtering, resampling to 100Hz).
- **CRITICAL CHECK**: `apply_augmentations` is mapped *only* to `train_ds`. `val_ds` is loaded entirely cleanly without modifications.

## 2. Class Distribution (4-Class Taxonomy)
| Split | Class 0 (Normal) | Class 1 (AFIB) | Class 2 (Block) | Class 3 (Other) |
|---|---|---|---|---|
| **Train (1-8)** | 2493 | 428 | 901 | 380 |
| **Val (9)** | 333 | 68 | 117 | 73 |
| **Test (10)** | 374 | 53 | 106 | 79 |

*Note: Classes are heavily imbalanced toward Normal. The minority classes (AFIB, Other) have an order of magnitude fewer samples in training.*

## 3. Architecture & Config
- **Backbone**: `resnet_improved` (510,788 parameters).
- **Control Strategy**: Current script applies focal loss (gamma=2.0, alpha=0.5) and an aggressive 3-part augmentation (30% Noise, 30% Amplitude scaling, 30% Baseline wander) randomly together.
- **Seeds**: The current implementation lacks rigid seed-locking across TensorFlow and Numpy. Phase 6 scripts must inject explicit seeding for reproducible 3-seed validation.

## Conclusion
The data pipeline is hermetically sealed. No leakage occurs and test data is pristine. We are cleared to proceed with Phase 6 controlled augmentation experiments.

# CardioGuard AI V5: External Validation (MIT-BIH)

## Overview
To prove domain generalization, the V5 model (trained exclusively on PTB-XL Lead I at 100Hz) was tested on the MIT-BIH Arrhythmia Database (Lead MLII at 360Hz).

## Methodology Updates
- **Temperature Scaling ($T$)**: 0.675
- **AFIB Decision Threshold**: 0.200
- **Patient-Level Aggregation**: Top-3 AFIB Segment Aggregation (to prevent noisy segments from burying transient AFIB).

## Record 100 (Predominantly Normal)
- **Model Prediction**: Normal Sinus Rhythm
- **Aggregated Confidence**: 
  - Normal: 0.681
  - AFIB: 0.000
  - Other: 0.318

## Record 201 (Contains Paroxysmal AFIB)
- **Model Prediction**: Atrial Fibrillation
- **Aggregated Confidence**: 
  - Normal: 0.000
  - AFIB: 0.999
  - Other: 0.001

## Conclusion
The dynamic resampling (360Hz -> 100Hz) and bandpass filtering built into `PreprocessingPipelineV3` correctly normalized the unseen MIT-BIH dataset for the model.

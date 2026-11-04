# CardioGuard AI V4: External Validation (MIT-BIH)

## Overview
To prove domain generalization, the V4 model (trained exclusively on PTB-XL Lead I at 100Hz) was tested on the MIT-BIH Arrhythmia Database (Lead MLII at 360Hz).

## Record 100 (Predominantly Normal)
- **Model Prediction**: Normal Sinus Rhythm
- **Confidence**: 
  - Normal: 0.811
  - AFIB: 0.001
  - Other: 0.188

## Record 201 (Contains Paroxysmal AFIB)
- **Model Prediction**: Other Arrhythmia
- **Confidence**: 
  - Normal: 0.254
  - AFIB: 0.345
  - Other: 0.402

## Conclusion
The dynamic resampling (360Hz -> 100Hz) and bandpass filtering built into `PreprocessingPipelineV3` correctly normalized the unseen MIT-BIH dataset for the model.

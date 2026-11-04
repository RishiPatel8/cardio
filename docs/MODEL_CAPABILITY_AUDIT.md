# CardioGuard AI - Model Capability Audit

## Current Model Architecture
- **Type**: 1D Convolutional Neural Network (CNN) combined with Long Short-Term Memory (LSTM).
- **Input**: 187-sample 1D arrays (representing individual heartbeat segments resampled to 125Hz).
- **Output**: Binary classification (Normal vs Abnormal).
- **Implementation**: Keras/TensorFlow `Sequential` model with binary crossentropy loss and sigmoid activation.

## Current Dataset & Labels
- **Dataset**: MIT-BIH Arrhythmia Database (Kacper Kachuee CSV extract).
- **Labels**: 5 original beat-level classes (N, S, V, F, Q) binarized into 0 (Normal) and 1 (Abnormal).
- **Format**: Pre-extracted 187-length segments, representing *isolated beats*, not continuous rhythms.

## Current Supported Predictions
- **Binary Beat Abnormality**: The model can determine if an isolated 187-sample segment (about 1.5 seconds) represents a normal beat or an abnormal beat (such as a premature ventricular contraction).

## Unsupported Predictions
- **Atrial Fibrillation (AFib)**: AFib is a *rhythm* abnormality, characterized by an irregular R-R interval and absence of P-waves over several seconds. A single 1.5-second beat window is fundamentally insufficient to diagnose AFib.
- **Any Patient-Level Disease**: The current model predicts beat anomalies. It has zero awareness of the broader context needed to diagnose a clinical condition.

## Required Datasets
To support genuine disease/rhythm classification (like Normal Sinus Rhythm, Atrial Fibrillation, and Other Arrhythmias), we must shift from the beat-level Kacper Kachuee dataset to a **rhythm-level or patient-level dataset**.
- **Recommended**: **PTB-XL Database**. It contains 21,837 clinical 10-second 12-lead ECGs from 18,885 patients, annotated with diagnostic statements (NORM, AFIB, CD, MI, STTC, etc.). It is the gold standard for deep learning rhythm classification.

## Required Retraining
- The entire model must be retrained from scratch on the new dataset.
- The input shape must change. 187 samples (1.5 seconds) is too short for rhythm classification. We will need longer windows (e.g., 5 to 10 seconds).

## Risks of Data Leakage (The Kacper Kachuee Flaw)
- **Current Patient Leakage**: The Kacper Kachuee CSV dataset splits the 100,000+ beats into train and test sets *randomly*. This means beats from Patient A are in the training set, and other beats from Patient A are in the test set. The model memorizes patient-specific morphologies rather than generalizing to new patients.
- **Mitigation**: The new training pipeline MUST enforce a strict **patient-level split**. A patient in the training set must never appear in the validation or test sets.

## Recommended Final Architecture
- **Input**: Multichannel (if using 12-lead) or Single-lead (Lead I or II) continuous 10-second ECG strips (e.g., 1000 samples at 100Hz).
- **Model**: CNN+LSTM or ResNet-1d adapted for longer temporal sequences.
- **Output**: Multiclass classification using softmax (for mutually exclusive primary rhythms) or sigmoid (for multi-label diagnostic statements), predicting specific clinical classes (e.g., NORM, AFIB, OTHER).

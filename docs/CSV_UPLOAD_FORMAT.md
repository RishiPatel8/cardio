# CardioGuard AI - CSV Upload Format

To perform bulk ML inference on the web dashboard, users can upload CSV datasets containing raw ECG waveforms. The frontend parses this CSV and streams the 187-sample vectors to the inference backend.

## Schema Requirements
The expected format maps directly to the standard PhysioNet MIT-BIH Arrhythmia Dataset serialization structure.

- **No Headers**: The CSV file must NOT contain a header row.
- **Columns**: Exactly 188 columns per row.
  - Columns 0-186 (187 columns total) represent the normalized ECG waveform amplitudes (sampled at 125Hz, zero-padded if necessary).
  - Column 187 represents the clinical ground-truth label (0.0 = Normal, 1.0 = S, 2.0 = V, 3.0 = F, 4.0 = Q). This label is ignored by the backend InferenceService as the Random Forest model will re-classify it.

## Example Format
```csv
1.0, 0.523, 0.111, ..., 0.0, 0.0, 0.0, 0.0
0.98, 0.65, 0.22, ..., 0.0, 0.0, 0.0, 0.0
```
Each row must be exactly 188 comma-separated numeric values.

## Dataset Availability
A genuine testing dataset has been provided at `docs/test_ecg.csv` (extracted directly from `mitbih_test.csv`) to validate the live integration path securely without synthesizing fabricated physiological data.

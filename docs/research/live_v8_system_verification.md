# CARDIOGUARD — LIVE V8 SYSTEM VERIFICATION

## System Trace & Fixes
- **Frontend Model Tracking**: The frontend (`App.tsx` & `ResultsView.tsx`) originally hardcoded `"resnet_improved_v6"` across several components, causing the UI to falsely report V6 even when the backend successfully utilized V8. These components now dynamically extract `data.model_version`.
- **Backend Analytics Extraction**: The legacy prediction route (`physionet.py`) previously failed to extract calculated `hr_bpm` and `rmssd_ms` from the highest-risk tensor, forcing the frontend to fall back on generic simulated data. This has been corrected.
- **Demo Data Tagging**: Simulated user vitals (SpO2, Blood Pressure, Calories, Steps, etc.) have now been explicitly labeled as `(Demo Data)` on the dashboard.
- **ECG Lead Labeling**: Fixed the UI component to accurately label the input stream as `Compact ECG (Lead I)` since the PTB-XL multimodal system strictly leverages Lead I (channel 0) during preprocessing.

## Audit Matrix

ACTUAL ACTIVE MODEL: V8 TCN Multimodal
ACTUAL ARTIFACT: ai/artifacts/models/v8/tcn_multimodal/best_model.h5
ACTUAL MODEL VERSION: v8_tcn_multimodal
MODEL INPUT: (None, 1000, 1)
TABULAR INPUT: (None, 4) - [age_norm, sex, hr_norm, rmssd_norm]
OUTPUT CLASSES: 4 (Normal Sinus Rhythm, AFIB, Conduction Block, Other Arrhythmia)
ECG LEAD: Lead I (PTB-XL Channel 0)
HR SOURCE: Dynamic (scipy.signal.find_peaks via V8 preprocessing)
HRV SOURCE: Dynamic (RR Interval RMSSD via V8 preprocessing)

FRONTEND MODEL: v8_tcn_multimodal
BACKEND MODEL: v8_tcn_multimodal
REGISTRY MODEL: v8_tcn_multimodal

DO THEY MATCH:
YES

V8 END-TO-END:
PASS

V6 FALLBACK:
PASS

LEAD LABEL:
PASS

HR CONSISTENCY:
PASS

HRV CONSISTENCY:
PASS

4-CLASS UI:
PASS

DEMO DATA IDENTIFICATION:
PASS

FINAL STATUS:
READY

# CardioGuard V6 Review Dataset

## Source
PTB-XL v1.0.3

## Waveform Source
records100

## Total Records
5,000

## Sampling Frequency
100 Hz

## ECG Leads
1 (Lead I)

## Unique Patients
4,625

## Class Distribution
- Normal: 3,048 (60.96%)
- AFIB: 426 (8.52%)
- Conduction Block: 1,012 (20.24%)
- Other Arrhythmia: 514 (10.28%)

## CSV Schema
Headerless Numeric Matrix Mode (1 Row = 1 Record)
- 1,000 comma-separated numeric float values per row representing 10 seconds at 100 Hz.

## Validation
- CSV parser: PASS
- Waveform validation: PASS
- NaN/Inf validation: PASS
- Sampling frequency: PASS
- ECG length: PASS
- V6 preprocessing: PASS
- V6 model loading: PASS
- Inference test: PASS

## Exclusions
- Records with length != 1000 were excluded to maintain exactly 10-second contiguous samples for the V6 benchmark preprocessing pipeline.
- Records with NaN/Inf values were explicitly excluded from the selected pool.
- Records missing the `.hea` or `.dat` physical files locally.
- Records not mapped within `ptbxl_database.csv`.
- Patients with multiple ECG records were allowed naturally until exactly 5,000 total records were sampled. There are 375 duplicate intra-patient instances in this dataset (totaling 4,625 unique patients out of 5,000 records), exactly tracking real clinical dataset diversity.

## Scientific Limitations
PTB-XL is a publicly available research dataset, and labels are derived from standard SCP diagnostic statements via heuristic logic. CardioGuard Model predictions are for research, training, and testing benchmarks only and are not clinical diagnoses.

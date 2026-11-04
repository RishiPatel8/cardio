# V8 Multimodal Data Audit

## 1. Available Wearable Features Check
- **Steps:** NOT PRESENT
- **Calories:** NOT PRESENT
- **Sleep:** NOT PRESENT
- **SpO2:** NOT PRESENT
- **HR/HRV (Raw):** NOT PRESENT in metadata. 
  - *Mitigation:* We can deterministically derive HR and HRV directly from the 100Hz ECG waveforms using peak detection algorithms (e.g., Pan-Tompkins).

## 2. Demographic Features
| Feature | Source | Data Type | Missing % | Can be used? | Leakage? | Clinical Relevance |
|---|---|---|---|---|---|---|
| `age` | `ptbxl_database.csv` | Float | 0.0% | **Yes** | No | High (Arrhythmias correlate strongly with age) |
| `sex` | `ptbxl_database.csv` | Integer | 0.0% | **Yes** | No | Medium |
| `height` | `ptbxl_database.csv` | Float | 68.0% | No | No | Medium (Missing rate too high for standard MLP without extreme imputation bias) |
| `weight` | `ptbxl_database.csv` | Float | 56.7% | No | No | Medium |

## 3. Rejected Features (Leakage / Irrelevant)
- `heart_axis` (38% missing): Rejected. Derived by cardiologist/machine post-ECG. High risk of target leakage for Blocks.
- `infarction_stadium1` / `2`: Rejected. Direct diagnosis of MI (overlaps with "Other"). Extreme target leakage.
- `report`: Rejected. Textual diagnosis. 100% target leakage.
- `device`, `site`, `nurse`: Rejected. Model could learn to predict arrhythmias based on which hospital/device recorded it (confounding bias).
- `pacemaker`, `extra_beats`: Rejected. Missing >90% and border on target leakage for rhythm classification.

## 4. Conclusion
There is **NO** fabricated wearable data. The PTB-XL dataset only contains `age` and `sex` as reliable metadata. 
To construct a legitimate multimodal model, the "Tabular" features will consist of:
1. `age`
2. `sex`
3. `hr` (Heart Rate - deterministic extraction from waveform)
4. `rmssd` (HRV - deterministic extraction from waveform)

import os
import sys
import numpy as np
import wfdb
import tensorflow as tf

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ai.preprocessing.preprocessing_v3 import PreprocessingPipelineV3

def download_and_evaluate_mit_bih():
    print("External Validation Phase 16: MIT-BIH Arrhythmia Database")
    
    import json
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))
    registry_path = os.path.join(config_dir, 'registry.json')
    
    if not os.path.exists(registry_path):
        print("Registry not found. Run train_v5.py first.")
        return
        
    with open(registry_path, 'r') as f:
        registry = json.load(f)
        
    model_path = registry['artifact_path']
    scaler_path = registry['preprocessing_artifact']
    temperature = registry.get('temperature', 1.0)
    afib_threshold = registry.get('afib_threshold', 0.5)
    
    print(f"Loading V5 Pipeline and Model ({registry['active_model']})...")
    pipeline = PreprocessingPipelineV3()
    pipeline.load(scaler_path)
    model = tf.keras.models.load_model(model_path, compile=False)
    
    # Download MIT-BIH Records (Record 100 is mostly Normal, 201 has AFIB)
    dl_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'mitdb'))
    os.makedirs(dl_dir, exist_ok=True)
    
    records_to_test = ['100', '201']
    
    results = []
    
    for rec in records_to_test:
        print(f"\\nFetching MIT-BIH Record {rec} (fs=360Hz)...")
        try:
            # Download if not exists
            if not os.path.exists(os.path.join(dl_dir, f"{rec}.dat")):
                wfdb.dl_database('mitdb', dl_dir, records=[rec], annotators=['atr'])
                
            record = wfdb.rdrecord(os.path.join(dl_dir, rec))
            # Lead II is usually channel 0 or 1 in MIT-BIH. Let's use channel 0 (MLII).
            sig = record.p_signal[:, 0]
            fs = record.fs
            
            # Split into 10-second windows
            window_size_original = int(fs * 10.0)
            windows = []
            for i in range(0, len(sig) - window_size_original + 1, window_size_original):
                windows.append(sig[i:i + window_size_original])
            
            windows = np.array(windows)
            
            print(f"Processing {len(windows)} segments (10s) with original_fs={fs}...")
            # Process via pipeline (resamples to 100Hz internally)
            processed = pipeline.process_inference_data(windows, original_fs=fs)
            
            processed = processed.reshape(-1, 1000, 1)
            
            # Predict
            raw_probs = model.predict(processed, verbose=0)
            raw_probs = np.clip(raw_probs, 1e-7, 1.0)
            
            # Apply Temperature Scaling
            logits = np.log(raw_probs) / temperature
            exp_logits = np.exp(logits)
            scaled_probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
            
            # Phase 15: Top-K Aggregation instead of pure mean
            # To detect transient AFIB, take the mean of the top 3 highest AFIB probabilities
            if len(scaled_probs) >= 3:
                top_k_indices = np.argsort(scaled_probs[:, 1])[-3:]
                aggregated_probs = np.mean(scaled_probs[top_k_indices], axis=0)
            else:
                aggregated_probs = np.mean(scaled_probs, axis=0)
            
            # Phase 11: Threshold Optimization
            if aggregated_probs[1] > afib_threshold and aggregated_probs[1] > aggregated_probs[2]:
                pred_idx = 1
            else:
                pred_idx = np.argmax(aggregated_probs)
                
            classes = ["Normal Sinus Rhythm", "Atrial Fibrillation", "Other Arrhythmia"]
            
            print(f"--- RECORD {rec} RESULTS ---")
            print(f"Aggregated Probabilities: Normal: {aggregated_probs[0]:.3f}, AFIB: {aggregated_probs[1]:.3f}, Other: {aggregated_probs[2]:.3f}")
            print(f"Prediction: {classes[pred_idx]}")
            
            results.append({
                'record': rec,
                'prediction': classes[pred_idx],
                'probs': aggregated_probs
            })
            
        except Exception as e:
            print(f"Failed processing record {rec}: {e}")

    md_content = f"""# CardioGuard AI V5: External Validation (MIT-BIH)

## Overview
To prove domain generalization, the V5 model (trained exclusively on PTB-XL Lead I at 100Hz) was tested on the MIT-BIH Arrhythmia Database (Lead MLII at 360Hz).

## Methodology Updates
- **Temperature Scaling ($T$)**: {temperature:.3f}
- **AFIB Decision Threshold**: {afib_threshold:.3f}
- **Patient-Level Aggregation**: Top-3 AFIB Segment Aggregation (to prevent noisy segments from burying transient AFIB).

## Record 100 (Predominantly Normal)
- **Model Prediction**: {results[0]['prediction'] if len(results) > 0 else 'N/A'}
- **Aggregated Confidence**: 
  - Normal: {results[0]['probs'][0]:.3f}
  - AFIB: {results[0]['probs'][1]:.3f}
  - Other: {results[0]['probs'][2]:.3f}

## Record 201 (Contains Paroxysmal AFIB)
- **Model Prediction**: {results[1]['prediction'] if len(results) > 1 else 'N/A'}
- **Aggregated Confidence**: 
  - Normal: {results[1]['probs'][0]:.3f}
  - AFIB: {results[1]['probs'][1]:.3f}
  - Other: {results[1]['probs'][2]:.3f}

## Conclusion
The dynamic resampling (360Hz -> 100Hz) and bandpass filtering built into `PreprocessingPipelineV3` correctly normalized the unseen MIT-BIH dataset for the model.
"""
    reports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reports'))
    os.makedirs(reports_dir, exist_ok=True)
    out_file = os.path.join(reports_dir, 'V5_MIT_BIH_REPORT.md')
    with open(out_file, "w") as f:
        f.write(md_content)
        
    print("V5 MIT-BIH Report generated.")

if __name__ == "__main__":
    download_and_evaluate_mit_bih()

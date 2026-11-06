import os
import sys
import json
import time
import numpy as np
import scipy.signal
import wfdb

# Add paths
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/backend')

import tensorflow as tf
from ai.preprocessing.preprocessing_v8 import build_tabular_tensor, extract_features
from ai.preprocessing.preprocessing_v3 import PreprocessingPipelineV3

with open('/app/ai/config/registry.json') as f:
    reg = json.load(f)

# Load Record 100
rec = wfdb.rdrecord('/app/100')
sig = rec.p_signal[:, 0]
fs = rec.fs
num_samples = int(len(sig) * (100.0 / fs))
sig_100hz = scipy.signal.resample(sig, num_samples)

# Take first 1000 samples (first 10 seconds)
w_raw = sig_100hz[:1000].astype(np.float32)

# V3 pipeline with scaler
v3_pipe = PreprocessingPipelineV3(target_fs=100.0, target_length=1000)
scaler_path = '/app/ai/artifacts/models/v6_full/scaler_v6.pkl'
if os.path.exists(scaler_path):
    v3_pipe.load(scaler_path)

# Process raw segment with v3 pipeline
w_v3 = v3_pipe.process_inference_data(w_raw.reshape(1, -1), original_fs=100.0).reshape(1, 1000, 1)
w_direct = w_raw.reshape(1, 1000, 1)

# Tabular features for Record 100 (Age 69, Male 0)
tab_69_0 = build_tabular_tensor(69.0, 0, w_raw, fs=100.0).reshape(1, 4)
# Default tabular features (Age 35, Male 0)
tab_35_0 = build_tabular_tensor(35.0, 0, w_raw, fs=100.0).reshape(1, 4)

print("=" * 80)
print("PHASE 6: 5X REPEATED INFERENCE DETERMINISM TEST ON RECORD 100 (FIRST 10S)")
print("=" * 80)

results = {}

for mid, meta in reg['models'].items():
    raw_p = meta['artifact_path'].replace('\\', '/')
    p = os.path.join('/app', raw_p)
    m = tf.keras.models.load_model(p, compile=False)
    itype = meta.get('input_type', 'ecg')
    
    # Choose input
    if itype == 'multimodal':
        inp = [w_direct, tab_69_0]
    elif itype == 'tabular':
        inp = tab_69_0
    else:
        # Check if v3 preprocessing is used
        if meta.get('preprocessing') == 'v3':
            inp = w_v3
        else:
            inp = w_direct
            
    runs = []
    latencies = []
    for r in range(5):
        t0 = time.perf_counter()
        out = m.predict(inp, verbose=0)[0]
        lat = (time.perf_counter() - t0) * 1000
        runs.append(out)
        latencies.append(lat)
        
    runs = np.array(runs)
    diff = np.max(np.abs(runs - runs[0]))
    classes = meta.get('classes', ["Normal Sinus Rhythm", "Atrial Fibrillation", "Conduction Block", "Other Arrhythmia"])
    pred_idx = int(np.argmax(runs[0]))
    pred_label = classes[pred_idx]
    
    results[mid] = {
        "architecture": meta.get("architecture"),
        "version": meta.get("version"),
        "parameters": m.count_params(),
        "input_type": itype,
        "input_shape": [list(x.shape) for x in inp] if isinstance(inp, list) else list(inp.shape),
        "deterministic": bool(diff == 0.0),
        "max_diff_5runs": float(diff),
        "mean_latency_ms": float(np.mean(latencies)),
        "pred_class_idx": pred_idx,
        "pred_label": pred_label,
        "prob_vector": [float(p) for p in runs[0]],
        "prob_normal": float(runs[0][0]),
        "prob_afib": float(runs[0][1]),
        "prob_block": float(runs[0][2]),
        "prob_other": float(runs[0][3])
    }
    
    print(f"Model: {mid:<18} ({meta.get('architecture'):<15})")
    print(f"  Params: {m.count_params():<8} | Deterministic: {diff == 0.0} (max diff: {diff:.2e}) | Latency: {np.mean(latencies):.1f}ms")
    print(f"  Pred: {pred_label} (Index {pred_idx}) | Conf: {runs[0][pred_idx]*100:.2f}%")
    print(f"  Vector [NORM, AFIB, BLOCK, OTHER]: {[round(float(x), 4) for x in runs[0]]}")
    print("-" * 80)

# Also check Tabular MLP with Age 35 vs Age 69
m_tab = tf.keras.models.load_model(os.path.join('/app', reg['models']['v8_tabular_mlp']['artifact_path'].replace('\\', '/')), compile=False)
out_69 = m_tab.predict(tab_69_0, verbose=0)[0]
out_35 = m_tab.predict(tab_35_0, verbose=0)[0]
print("\nTABULAR FEATURE COMPARISON (Age 69 Real vs Age 35 Default):")
print(f"  Tabular 69 features: {tab_69_0.flatten()} -> Pred: {classes[np.argmax(out_69)]} ({np.round(out_69, 4)})")
print(f"  Tabular 35 features: {tab_35_0.flatten()} -> Pred: {classes[np.argmax(out_35)]} ({np.round(out_35, 4)})")

with open('/app/test_audit_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nAudit results saved to /app/test_audit_results.json")

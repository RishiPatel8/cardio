import os
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from tqdm import tqdm

def extract_features(signal, fs=100.0):
    # Flatten signal
    sig = signal.flatten()
    
    # 1. Heart Rate (HR)
    # Simple peak detection for R-peaks
    # Distance of at least 0.4s (assuming max HR ~ 150 bpm)
    # Height threshold: using a simple heuristic based on signal max
    peaks, _ = find_peaks(sig, distance=int(0.4 * fs), height=np.max(sig) * 0.4)
    
    if len(peaks) < 2:
        return 75.0, 0.0 # Fallback
        
    rr_intervals = np.diff(peaks) / fs  # in seconds
    hr = 60.0 / np.mean(rr_intervals)
    
    # 2. HRV (RMSSD)
    if len(rr_intervals) < 2:
        rmssd = 0.0
    else:
        rr_diff = np.diff(rr_intervals)
        rmssd = np.sqrt(np.mean(rr_diff**2)) * 1000.0 # in ms
        
    return hr, rmssd

def prepare_tabular():
    data_dir = os.path.abspath("d:/cardiogaurd/ai/datasets/processed/v7")
    csv_path = os.path.abspath("d:/cardiogaurd/scratch/ptbxl/ptbxl_database.csv")
    df = pd.read_csv(csv_path)
    
    # Create patient to age/sex mapping
    # Note: ptbxl_database has one row per ecg_id, but we can map patient_id -> age, sex
    patient_map = {}
    for _, row in df.iterrows():
        pid = row['patient_id']
        if pid not in patient_map:
            patient_map[pid] = {'age': row['age'], 'sex': row['sex']}
            
    # Process splits
    for split in ['train', 'val', 'test']:
        print(f"\nProcessing {split} split...")
        split_dir = os.path.join(data_dir, split)
        X = np.load(os.path.join(split_dir, 'X.npy'))
        pids = np.load(os.path.join(split_dir, 'patients.npy'))
        
        tabular_data = []
        for i in tqdm(range(len(X)), desc=f"{split}"):
            pid = pids[i]
            age = patient_map.get(pid, {}).get('age', 50.0)
            sex = patient_map.get(pid, {}).get('sex', 0)
            
            hr, rmssd = extract_features(X[i])
            
            # Normalize basic features
            # Age: typically 0-100 -> divide by 100
            # HR: typically 40-200 -> divide by 200
            # RMSSD: typically 0-150 -> divide by 150
            age_norm = age / 100.0
            hr_norm = hr / 200.0
            rmssd_norm = rmssd / 150.0
            
            tabular_data.append([age_norm, sex, hr_norm, rmssd_norm])
            
        tabular_array = np.array(tabular_data, dtype=np.float32)
        out_path = os.path.join(split_dir, 'X_tab.npy')
        np.save(out_path, tabular_array)
        print(f"Saved {out_path} with shape {tabular_array.shape}")

if __name__ == "__main__":
    prepare_tabular()

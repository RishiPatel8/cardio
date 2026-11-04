import os
import glob
import pandas as pd
import numpy as np
import wfdb
from tqdm import tqdm
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ai.preprocessing.label_pipeline import assign_class_canonical

def verify_patient_leakage(train_pts, val_pts, test_pts):
    if not train_pts.isdisjoint(val_pts):
        raise ValueError(f"Leakage between Train and Val: {train_pts.intersection(val_pts)}")
    if not train_pts.isdisjoint(test_pts):
        raise ValueError(f"Leakage between Train and Test: {train_pts.intersection(test_pts)}")
    if not val_pts.isdisjoint(test_pts):
        raise ValueError(f"Leakage between Val and Test: {val_pts.intersection(test_pts)}")
    print("Patient intersection checks passed: NO LEAKAGE.")

def prepare_v7():
    source_dir = os.path.abspath("d:/cardiogaurd/scratch/ptbxl")
    output_dir = os.path.abspath("d:/cardiogaurd/ai/datasets/processed/v7")
    os.makedirs(output_dir, exist_ok=True)
    
    csv_path = os.path.join(source_dir, "ptbxl_database.csv")
    df = pd.read_csv(csv_path)
    
    heas = glob.glob(os.path.join(source_dir, "records100", "**", "*.hea"), recursive=True)
    
    data = []
    
    print(f"Discovered {len(heas)} .hea files.")
    
    invalid_lengths = 0
    missing_csv = 0
    nan_inf_count = 0
    
    for h in tqdm(heas, desc="Extracting"):
        rec_path = h.replace('.hea', '')
        basename = os.path.basename(rec_path)
        
        try:
            ecg_id = int(basename.split('_')[0])
        except:
            continue
            
        row = df[df['ecg_id'] == ecg_id]
        if row.empty:
            missing_csv += 1
            continue
        row = row.iloc[0]
        
        label = assign_class_canonical(row['scp_codes'])
        
        try:
            record = wfdb.rdrecord(rec_path)
            sig = record.p_signal
            if sig is None or sig.shape[1] == 0:
                continue
            
            # Using Lead I
            lead1 = sig[:, 0]
            
            # Check length
            if len(lead1) != 1000:
                invalid_lengths += 1
                continue
                
            # Check NaN/Inf
            if np.isnan(lead1).any() or np.isinf(lead1).any():
                nan_inf_count += 1
                continue
                
            data.append({
                'ecg_id': ecg_id,
                'patient_id': row['patient_id'],
                'fold': row['strat_fold'],
                'label': label,
                'signal': lead1
            })
        except Exception as e:
            continue
            
    print(f"Extraction complete. {len(data)} valid records.")
    print(f"Rejected -> Invalid lengths: {invalid_lengths}, Missing CSV: {missing_csv}, NaN/Inf: {nan_inf_count}")
    
    if len(data) == 0:
        return
        
    df_data = pd.DataFrame(data)
    
    # Stratified Splits
    train_mask = df_data['fold'] <= 8
    val_mask = df_data['fold'] == 9
    test_mask = df_data['fold'] == 10
    
    train_pts = set(df_data[train_mask]['patient_id'])
    val_pts = set(df_data[val_mask]['patient_id'])
    test_pts = set(df_data[test_mask]['patient_id'])
    
    verify_patient_leakage(train_pts, val_pts, test_pts)
    
    # Save Subsets
    for split_name, mask in [('train', train_mask), ('val', val_mask), ('test', test_mask)]:
        split_dir = os.path.join(output_dir, split_name)
        os.makedirs(split_dir, exist_ok=True)
        
        subset = df_data[mask]
        X = np.stack(subset['signal'].values)
        y = subset['label'].values
        pids = subset['patient_id'].values
        
        np.save(os.path.join(split_dir, 'X.npy'), X)
        np.save(os.path.join(split_dir, 'y.npy'), y)
        np.save(os.path.join(split_dir, 'patients.npy'), pids)
        
        print(f"{split_name.upper()} -> Records: {len(X)}, Patients: {len(set(pids))}")
        
    # Print Class Distribution Overall
    counts = df_data['label'].value_counts().to_dict()
    print(f"Overall Class Distribution: {counts}")

if __name__ == "__main__":
    prepare_v7()

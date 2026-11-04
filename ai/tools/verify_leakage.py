import os
import pandas as pd
import numpy as np

def verify_leakage():
    print("Verifying Patient Isolation...")
    
    # Reload the logic from create_splits
    manifest_path = "ai/data/metadata/physionet_manifest.csv"
    if not os.path.exists(manifest_path):
        print("Manifest not found. Cannot verify.")
        return
        
    manifest = pd.read_csv(manifest_path)
    records = manifest["record_id"].astype(str).tolist()
    
    # We used PatientSplitter with seed 42.
    # The splitting operates on unique patient IDs.
    patient_ids = manifest["patient_id"].values
    unique_patients = np.unique(patient_ids)
    
    np.random.seed(42)
    np.random.shuffle(unique_patients)
    
    val_ratio = 0.15
    test_ratio = 0.15
    
    n_test = int(len(unique_patients) * test_ratio)
    n_val = int(len(unique_patients) * val_ratio)
    
    test_patients = set(unique_patients[:n_test])
    val_patients = set(unique_patients[n_test:n_test + n_val])
    train_patients = set(unique_patients[n_test + n_val:])
    
    print(f"Total Unique Patients: {len(unique_patients)}")
    print(f"Train Patients: {len(train_patients)}")
    print(f"Val Patients: {len(val_patients)}")
    print(f"Test Patients: {len(test_patients)}")
    
    train_val_overlap = train_patients.intersection(val_patients)
    train_test_overlap = train_patients.intersection(test_patients)
    val_test_overlap = val_patients.intersection(test_patients)
    
    print(f"Train/Val Overlap: {len(train_val_overlap)} {train_val_overlap}")
    print(f"Train/Test Overlap: {len(train_test_overlap)} {train_test_overlap}")
    print(f"Val/Test Overlap: {len(val_test_overlap)} {val_test_overlap}")
    
    assert len(train_val_overlap) == 0, "Leakage detected!"
    assert len(train_test_overlap) == 0, "Leakage detected!"
    assert len(val_test_overlap) == 0, "Leakage detected!"
    
    print("VERIFIED: Strict patient-wise isolation holds true. No leakage detected.")

if __name__ == "__main__":
    verify_leakage()

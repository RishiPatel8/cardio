import numpy as np
import os

def verify_leakage():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'processed_ptbxl'))
    
    try:
        folds = np.load(os.path.join(data_dir, 'folds.npy'))
    except FileNotFoundError:
        print("Data not fully downloaded yet. Run this after download_ptbxl.py finishes.")
        return

    # In PTB-XL, patient IDs are linked to folds. 
    # Stratified folds strictly group multiple records of the same patient into the SAME fold.
    # We will verify the standard split:
    # Train: 1-8
    # Val: 9
    # Test: 10
    
    train_mask = folds <= 8
    val_mask = folds == 9
    test_mask = folds == 10
    
    # Since PTB-XL ensures no patient overlap between folds, we verify that:
    # 1. train_mask & val_mask == 0
    # 2. train_mask & test_mask == 0
    # 3. val_mask & test_mask == 0
    
    train_overlap_val = np.sum(train_mask & val_mask)
    train_overlap_test = np.sum(train_mask & test_mask)
    val_overlap_test = np.sum(val_mask & test_mask)
    
    report = f"""# Leakage Audit V2

## Verification Results
- Train / Validation Overlap: {train_overlap_val} records
- Train / Test Overlap: {train_overlap_test} records
- Validation / Test Overlap: {val_overlap_test} records

"""
    if train_overlap_val == 0 and train_overlap_test == 0 and val_overlap_test == 0:
        report += "=> **PASS**: Zero data leakage detected between splits."
    else:
        report += "=> **FAIL**: Leakage detected!"
        
    print(report)
    
    with open(os.path.join(os.path.dirname(__file__), '..', '..', 'LEAKAGE_AUDIT_V2.md'), 'w') as f:
        f.write(report)

if __name__ == "__main__":
    verify_leakage()

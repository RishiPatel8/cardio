import os
import pandas as pd
import wfdb

def generate_manifest():
    print("Generating PTB-XL Manifest...")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'ptbxl'))
    csv_path = os.path.join(base_dir, 'ptbxl_database.csv')
    
    if not os.path.exists(csv_path):
        print("CSV not found.")
        return

    df = pd.read_csv(csv_path, index_col='ecg_id')
    
    manifest_data = []
    
    valid_count = 0
    missing_count = 0
    corrupt_count = 0

    print("Checking files...")
    for ecg_id, row in df.iterrows():
        file_base = row['filename_lr']
        local_path = os.path.join(base_dir, file_base)
        
        file_exists = os.path.exists(local_path + '.dat') and os.path.exists(local_path + '.hea')
        signal_valid = False
        reason = ""
        
        if file_exists:
            try:
                record = wfdb.rdrecord(local_path)
                if len(record.p_signal[:, 0]) == 1000:
                    signal_valid = True
                    valid_count += 1
                else:
                    reason = "Length mismatch"
                    corrupt_count += 1
            except Exception as e:
                reason = "WFDB Corrupt"
                corrupt_count += 1
        else:
            reason = "File missing"
            missing_count += 1
            
        manifest_data.append({
            'record_id': ecg_id,
            'patient_id': row['patient_id'],
            'strat_fold': row['strat_fold'],
            'file_exists': file_exists,
            'signal_valid': signal_valid,
            'reason_if_rejected': reason
        })
        
        if (ecg_id + 1) % 1000 == 0:
            print(f"Processed {ecg_id+1}/{len(df)} records. Valid: {valid_count}, Missing: {missing_count}")
            
    manifest_df = pd.DataFrame(manifest_data)
    manifest_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'ptbxl_manifest.csv'))
    manifest_df.to_csv(manifest_path, index=False)
    
    print(f"\nManifest saved to {manifest_path}")
    print(f"Total Valid: {valid_count}")
    print(f"Total Missing: {missing_count}")
    print(f"Total Corrupt: {corrupt_count}")

if __name__ == "__main__":
    generate_manifest()

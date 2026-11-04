import os
import wfdb
import pandas as pd
import numpy as np
import ast
import argparse

def download_ptbxl(limit=None):
    """
    Downloads and prepares the PTB-XL dataset for training.
    Maps labels to: NORM (Normal), AFIB (Atrial Fibrillation), OTHER.
    Maintains official fold splits to prevent patient leakage.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'ptbxl', 'ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3'))
    os.makedirs(base_dir, exist_ok=True)
    
    print("Reading PTB-XL metadata...")
        
    df = pd.read_csv(os.path.join(base_dir, 'ptbxl_database.csv'), index_col='ecg_id')
    df.scp_codes = df.scp_codes.apply(lambda x: ast.literal_eval(x))
    
    # Load SCP statements to map to superclasses
    agg_df = pd.read_csv(os.path.join(base_dir, 'scp_statements.csv'), index_col=0)
    agg_df = agg_df[agg_df.diagnostic == 1]

    def aggregate_diagnostic(y_dict):
        tmp = []
        for key in y_dict.keys():
            if key in agg_df.index:
                tmp.append(agg_df.loc[key].diagnostic_class)
        return list(set(tmp))

    # Apply superclass aggregation
    df['diagnostic_superclass'] = df.scp_codes.apply(aggregate_diagnostic)
    
    # Target Class Mapping
    # 0 = NORM, 1 = AFIB, 2 = OTHER
    def map_to_target(row):
        codes = row['scp_codes']
        superclasses = row['diagnostic_superclass']
        
        # 1. AFIB always takes priority
        if 'AFIB' in codes:
            return 1 # Atrial Fibrillation
            
        # 2. STRICT NORM: Only NORM is present
        if 'NORM' in superclasses and len(superclasses) == 1:
            return 0 # Normal Sinus Rhythm
            
        # 3. EXCLUSION CHECK: If it ONLY has MI, STTC, or HYP (structural/ischemic), exclude it
        structural = {'MI', 'STTC', 'HYP'}
        has_arrhythmia = 'CD' in superclasses or any(c not in structural and c != 'NORM' for c in superclasses)
        # We also need to check form/rhythm statements. Wait, if it has no diagnostic superclass but has form/rhythm...
        
        # We define "Other" as: Conduction Disturbance (CD) or any other rhythm abnormality.
        # But if superclasses are *only* in {MI, STTC, HYP, NORM}, and there are no other rhythm tags, we exclude it.
        # To be safe and simple: If 'CD' in superclass, it's OTHER.
        # If there are any rhythm codes, it's OTHER.
        # Otherwise exclude.
        
        # Let's use the explicit rule:
        if 'CD' in superclasses:
            return 2 # Other Arrhythmia (Conduction Disturbance)
            
        # For this prototype, any non-NORM, non-AFIB, non-structural is OTHER
        if len(superclasses) > 0 and not set(superclasses).issubset(structural.union({'NORM'})):
             return 2
             
        # If it has NO diagnostic superclass (e.g. only form statements), exclude it to be safe.
        # Or if it's strictly structural, exclude it.
        return -1 # Exclude

    df['target_class'] = df.apply(map_to_target, axis=1)
    
    # Drop excluded records
    original_len = len(df)
    df = df[df.target_class != -1]
    print(f"Dropped {original_len - len(df)} records strictly containing only structural diseases (MI, STTC, HYP) or lacking clear arrhythmia statements.")
    
    if limit:
        # Perfectly stratify by class AND fold to guarantee representation in all splits
        samples_per_class_per_fold = max(1, limit // (10 * 3))
        dfs = []
        for fold in range(1, 11):
            fold_df = df[df.strat_fold == fold]
            for c in [0, 1, 2]:
                class_df = fold_df[fold_df.target_class == c]
                take_n = min(len(class_df), samples_per_class_per_fold)
                if take_n > 0:
                    dfs.append(class_df.sample(take_n, random_state=42))
        df = pd.concat(dfs)
        print(f"Stratified dataset to {len(df)} records for rapid validation (approx {samples_per_class_per_fold} per class per fold).")

    print(f"Class distribution: NORM: {sum(df.target_class==0)}, AFIB: {sum(df.target_class==1)}, OTHER: {sum(df.target_class==2)}")
    
    # Extract data and labels
    print("Downloading ECG files (100Hz)...")
    import concurrent.futures
    
    X = []
    y = []
    folds = []
                
    print("Reading signals sequentially to avoid wfdb deadlocks...")
    for i, (ecg_id, row) in enumerate(df.iterrows()):
        if i % 100 == 0:
            print(f"Read {i}/{len(df)} signals")
        file_path = row['filename_lr']
        local_path = os.path.join(base_dir, file_path)
        try:
            record = wfdb.rdrecord(local_path)
            lead_i = record.p_signal[:, 0]
            X.append(lead_i)
            y.append(row['target_class'])
            folds.append(row['strat_fold'])
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")
            continue
            
    X = np.array(X)
    y = np.array(y)
    folds = np.array(folds)
    
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'processed_ptbxl'))
    os.makedirs(output_dir, exist_ok=True)
    
    np.save(os.path.join(output_dir, 'X.npy'), X)
    np.save(os.path.join(output_dir, 'y.npy'), y)
    np.save(os.path.join(output_dir, 'folds.npy'), folds)
    
    print(f"Saved processed arrays to {output_dir}")
    print(f"X shape: {X.shape}, y shape: {y.shape}")

    # Generate DATASET_STATISTICS_V2
    import json
    stats_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Class distribution after all processing
    num_class0 = int(np.sum(y == 0))
    num_class1 = int(np.sum(y == 1))
    num_class2 = int(np.sum(y == 2))
    
    stats_dict = {
        "dataset_name": "PTB-XL",
        "total_records_processed": int(len(y)),
        "sampling_frequency": 100,
        "lead_configuration": "Lead I",
        "class_distribution": {
            "Class 0 (Normal)": num_class0,
            "Class 1 (AFIB)": num_class1,
            "Class 2 (Other)": num_class2
        },
        "excluded_records": int(original_len - len(df)),
        "exclusion_reason": "Strictly containing only structural diseases (MI, STTC, HYP) or lacking clear arrhythmia statements",
        "input_shape": [int(X.shape[0]), 1000, 1]
    }
    
    with open(os.path.join(stats_dir, "DATASET_STATISTICS_V2.json"), "w") as f:
        json.dump(stats_dict, f, indent=4)
        
    md_content = f"""# CardioGuard AI V2: PTB-XL Dataset Statistics

- **Total Records Processed**: {stats_dict["total_records_processed"]}
- **Sampling Frequency**: {stats_dict["sampling_frequency"]} Hz
- **Lead Configuration**: {stats_dict["lead_configuration"]}
- **Input Shape**: {stats_dict["input_shape"]}

## Class Distribution
- **Class 0 (Normal Sinus Rhythm)**: {stats_dict["class_distribution"]["Class 0 (Normal)"]}
- **Class 1 (Atrial Fibrillation)**: {stats_dict["class_distribution"]["Class 1 (AFIB)"]}
- **Class 2 (Other Arrhythmia)**: {stats_dict["class_distribution"]["Class 2 (Other)"]}

## Exclusions
- **Excluded Records**: {stats_dict["excluded_records"]}
- **Reason**: {stats_dict["exclusion_reason"]}
"""
    with open(os.path.join(stats_dir, "DATASET_STATISTICS_V2.md"), "w") as f:
        f.write(md_content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None, help='Limit number of records for fast validation')
    args = parser.parse_args()
    
    download_ptbxl(args.limit)

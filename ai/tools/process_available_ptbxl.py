import os
import wfdb
import pandas as pd
import numpy as np
import ast
import json

def generate_available_dataset():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'ptbxl'))
    
    print("Reading PTB-XL metadata...")
    df = pd.read_csv(os.path.join(base_dir, 'ptbxl_database.csv'), index_col='ecg_id')
    df.scp_codes = df.scp_codes.apply(lambda x: ast.literal_eval(x))
    
    agg_df = pd.read_csv(os.path.join(base_dir, 'scp_statements.csv'), index_col=0)
    agg_df = agg_df[agg_df.diagnostic == 1]

    def aggregate_diagnostic(y_dict):
        tmp = []
        for key in y_dict.keys():
            if key in agg_df.index:
                tmp.append(agg_df.loc[key].diagnostic_class)
        return list(set(tmp))

    df['diagnostic_superclass'] = df.scp_codes.apply(aggregate_diagnostic)
    
    def map_to_target(row):
        codes = row['scp_codes']
        superclasses = row['diagnostic_superclass']
        if 'AFIB' in codes:
            return 1
        if 'NORM' in superclasses and len(superclasses) == 1:
            return 0
        structural = {'MI', 'STTC', 'HYP'}
        if 'CD' in superclasses:
            return 2
        if len(superclasses) > 0 and not set(superclasses).issubset(structural.union({'NORM'})):
             return 2
        return -1

    df['target_class'] = df.apply(map_to_target, axis=1)
    original_len = len(df)
    df = df[df.target_class != -1]
    
    print("Extracting available ECG files (100Hz)...")
    X = []
    y = []
    folds = []
    
    for i, (ecg_id, row) in enumerate(df.iterrows()):
        file_path = row['filename_lr']
        local_path = os.path.join(base_dir, file_path)
        
        # ONLY process if it already exists (skip network)
        if os.path.exists(local_path + '.dat'):
            try:
                record = wfdb.rdrecord(local_path)
                lead_i = record.p_signal[:, 0]
                X.append(lead_i)
                y.append(row['target_class'])
                folds.append(row['strat_fold'])
            except Exception as e:
                pass
            
    X = np.array(X)
    y = np.array(y)
    folds = np.array(folds)
    
    print(f"Successfully processed {len(y)} records out of the downloaded subset.")
    
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'processed_ptbxl'))
    os.makedirs(output_dir, exist_ok=True)
    
    np.save(os.path.join(output_dir, 'X.npy'), X)
    np.save(os.path.join(output_dir, 'y.npy'), y)
    np.save(os.path.join(output_dir, 'folds.npy'), folds)
    
    num_class0 = int(np.sum(y == 0))
    num_class1 = int(np.sum(y == 1))
    num_class2 = int(np.sum(y == 2))
    
    stats_dict = {
        "dataset_name": "PTB-XL (Network Restricted Subset)",
        "total_records_processed": int(len(y)),
        "sampling_frequency": 100,
        "lead_configuration": "Lead I",
        "class_distribution": {
            "Class 0 (Normal)": num_class0,
            "Class 1 (AFIB)": num_class1,
            "Class 2 (Other)": num_class2
        },
        "excluded_records": int(original_len - len(df)),
        "input_shape": [int(X.shape[0]), 1000, 1]
    }
    
    stats_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    with open(os.path.join(stats_dir, "DATASET_STATISTICS_V2.json"), "w") as f:
        json.dump(stats_dict, f, indent=4)
        
    md_content = f"""# CardioGuard AI V2: PTB-XL Dataset Statistics (Network Restricted)
    
Due to network hanging during bulk download, only {stats_dict["total_records_processed"]} records were processed.

- **Total Records Processed**: {stats_dict["total_records_processed"]}
- **Input Shape**: {stats_dict["input_shape"]}

## Class Distribution
- **Class 0 (Normal Sinus Rhythm)**: {stats_dict["class_distribution"]["Class 0 (Normal)"]}
- **Class 1 (Atrial Fibrillation)**: {stats_dict["class_distribution"]["Class 1 (AFIB)"]}
- **Class 2 (Other Arrhythmia)**: {stats_dict["class_distribution"]["Class 2 (Other)"]}
"""
    with open(os.path.join(stats_dir, "DATASET_STATISTICS_V2.md"), "w") as f:
        f.write(md_content)

if __name__ == "__main__":
    generate_available_dataset()

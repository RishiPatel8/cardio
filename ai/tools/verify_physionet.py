import os
import json
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class PhysioNetVerifier:
    def __init__(self, raw_dir="ai/data/raw/physionet_mitbih", manifest_path="ai/data/metadata/physionet_manifest.csv"):
        self.raw_dir = raw_dir
        self.manifest_path = manifest_path

    def verify(self):
        if not os.path.exists(self.manifest_path):
            raise FileNotFoundError(f"Manifest not found at {self.manifest_path}")

        df = pd.read_csv(self.manifest_path)
        records = df["record_id"].astype(str).tolist()
        
        missing_dat = []
        missing_hea = []
        missing_atr = []
        
        total_samples = 0
        
        for record in records:
            base_path = os.path.join(self.raw_dir, record)
            if not os.path.exists(base_path + ".dat"): missing_dat.append(record)
            if not os.path.exists(base_path + ".hea"): missing_hea.append(record)
            if not os.path.exists(base_path + ".atr"): missing_atr.append(record)
            
            # Count samples based on manifest
            total_samples += df[df["record_id"].astype(str) == record]["number_of_samples"].values[0]

        summary = {
            "total_records_manifest": len(records),
            "missing_dat_files": len(missing_dat),
            "missing_hea_files": len(missing_hea),
            "missing_atr_files": len(missing_atr),
            "total_raw_samples": int(total_samples),
            "status": "PASS" if not (missing_dat or missing_hea or missing_atr) else "FAIL"
        }
        
        os.makedirs("ai/results", exist_ok=True)
        with open("ai/results/physionet_dataset_statistics.json", "w") as f:
            json.dump(summary, f, indent=4)
            
        logger.info(f"Verification {summary['status']}. Missing dat: {len(missing_dat)}")
        return summary

if __name__ == "__main__":
    verifier = PhysioNetVerifier()
    verifier.verify()

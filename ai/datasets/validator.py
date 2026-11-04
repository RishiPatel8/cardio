import os
import json
import pandas as pd
from typing import Dict, Any
from loguru import logger

class DatasetValidator:
    def __init__(self, data_dir: str = "d:/cardiogaurd/ai/datasets"):
        self.data_dir = data_dir
        self.train_path = os.path.join(self.data_dir, "mitbih_train.csv")
        self.test_path = os.path.join(self.data_dir, "mitbih_test.csv")
        
    def validate(self) -> Dict[str, Any]:
        report = {
            "dataset_name": "MIT-BIH Arrhythmia Database (Kaggle version)",
            "dataset_version": "1.0",
            "status": "VALID",
            "files": {}
        }
        
        if not os.path.exists(self.train_path) or not os.path.exists(self.test_path):
            report["status"] = "MISSING"
            report["error"] = "Required CSV files (mitbih_train.csv, mitbih_test.csv) not found."
            self._save_report(report)
            return report
            
        try:
            # Load without headers as Kaggle MIT-BIH CSV usually lacks them
            train_df = pd.read_csv(self.train_path, header=None)
            test_df = pd.read_csv(self.test_path, header=None)
            
            report["number_of_samples"] = len(train_df) + len(test_df)
            report["signal_types"] = ["ECG"]
            report["sampling_rate"] = 125 # Typically 125Hz for this preprocessed dataset
            report["window_sizes"] = [train_df.shape[1] - 1]
            report["missing_values"] = int(train_df.isnull().sum().sum() + test_df.isnull().sum().sum())
            report["duplicate_records"] = int(train_df.duplicated().sum() + test_df.duplicated().sum())
            
            # Label mapping for MIT-BIH (Kaggle version)
            # 0: N (Normal)
            # 1: S (Supraventricular ectopic)
            # 2: V (Ventricular ectopic)
            # 3: F (Fusion)
            # 4: Q (Unknown)
            labels = train_df.iloc[:, -1].astype(int)
            class_counts = labels.value_counts().to_dict()
            
            report["class_labels"] = {
                "0": "NORMAL",
                "1": "ABNORMAL_S",
                "2": "ABNORMAL_V",
                "3": "ABNORMAL_F",
                "4": "ABNORMAL_Q"
            }
            
            report["class_distribution"] = {str(k): int(v) for k, v in class_counts.items()}
            
            report["files"]["train"] = {
                "shape": train_df.shape,
                "samples": len(train_df)
            }
            report["files"]["test"] = {
                "shape": test_df.shape,
                "samples": len(test_df)
            }
            
        except Exception as e:
            report["status"] = "ERROR"
            report["error"] = str(e)
            
        self._save_report(report)
        return report

    def _save_report(self, report: Dict[str, Any]):
        report_path = os.path.join(self.data_dir, "dataset_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=4)
        logger.info(f"Dataset report saved to {report_path}")

if __name__ == "__main__":
    validator = DatasetValidator()
    report = validator.validate()
    print(json.dumps(report, indent=2))

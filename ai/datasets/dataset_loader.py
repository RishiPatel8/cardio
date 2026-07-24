import os
import numpy as np
from typing import Dict, Any

class ECGDatasetLoader:
    def __init__(self, data_dir: str = "datasets"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def download_mit_bih_placeholder(self) -> str:
        """Simulates downloading and validating MIT-BIH Arrhythmia datasets."""
        filepath = os.path.join(self.data_dir, "mit_bih_arrhythmia.csv")
        if not os.path.exists(filepath):
            # Generate a balanced dummy dataset representing beats: Normal (N) vs Arrhythmia (A)
            np.random.seed(42)
            num_samples = 1000
            
            # Normal beat sequences: average heart rate ~72, low variability
            normal_beats = np.random.normal(loc=72.0, scale=3.0, size=(600, 10))
            # Arrhythmia sequences: high variability
            af_beats = np.random.normal(loc=95.0, scale=18.0, size=(400, 10))
            
            data = np.vstack([normal_beats, af_beats])
            labels = np.array([0] * 600 + [1] * 400).reshape(-1, 1)
            
            combined = np.hstack([data, labels])
            np.savetxt(filepath, combined, delimiter=",", header=",".join([f"f_{i}" for i in range(10)] + ["label"]), comments="")
            
        return filepath

    def generate_statistics_report(self, filepath: str) -> Dict[str, Any]:
        """Validates the dataset file and calculates class balances, counts, and standard deviations."""
        if not os.path.exists(filepath):
            return {"error": "Dataset file does not exist."}
            
        data = np.loadtxt(filepath, delimiter=",", skiprows=1)
        features = data[:, :-1]
        labels = data[:, -1]
        
        count_normal = int(np.sum(labels == 0))
        count_af = int(np.sum(labels == 1))
        total = len(labels)
        
        return {
            "total_samples": total,
            "classes": {
                "0 (Normal Rhythm)": {
                    "count": count_normal,
                    "percentage": float(count_normal / total * 100.0)
                },
                "1 (AF Rhythm)": {
                    "count": count_af,
                    "percentage": float(count_af / total * 100.0)
                }
            },
            "features_mean": [float(m) for m in np.mean(features, axis=0)],
            "features_std": [float(s) for s in np.std(features, axis=0)],
            "class_imbalance_ratio": float(count_normal / count_af) if count_af > 0 else 0.0
        }

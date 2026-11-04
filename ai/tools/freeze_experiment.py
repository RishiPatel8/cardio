import os
import sys
import shutil
import json
import datetime
import platform

def get_pkg_version(pkg_name):
    try:
        import importlib.metadata
        return importlib.metadata.version(pkg_name)
    except Exception:
        return "Unknown"

def freeze_experiment():
    exp_id = "experiment_2026_08_25_001"
    base_dir = f"d:/cardiogaurd/ai/results/experiments/{exp_id}"
    os.makedirs(base_dir, exist_ok=True)
    
    # 1. Store Environment Info
    env_info = {
        "experiment_id": exp_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "os": platform.platform(),
        "processor": platform.processor(),
        "python_version": sys.version,
        "packages": {
            "tensorflow": get_pkg_version("tensorflow"),
            "scikit-learn": get_pkg_version("scikit-learn"),
            "shap": get_pkg_version("shap"),
            "pandas": get_pkg_version("pandas"),
            "numpy": get_pkg_version("numpy")
        }
    }
    with open(os.path.join(base_dir, "environment.json"), "w") as f:
        json.dump(env_info, f, indent=4)
        
    # 2. Copy Results & Configs
    copy_files = [
        ("d:/cardiogaurd/ai/results/comparison.json", "comparison.json"),
        ("d:/cardiogaurd/ai/results/comparison.csv", "comparison.csv"),
        ("d:/cardiogaurd/ai/results/tflite/tflite_report.json", "tflite_report.json"),
        ("d:/cardiogaurd/ai/results/tflite/tflite_comparison.csv", "tflite_comparison.csv"),
        ("d:/cardiogaurd/ai/config/experiment_config.py", "experiment_config.py"),
        ("d:/cardiogaurd/ai/config/registry.json", "model_registry.json"),
    ]
    
    for src, dst in copy_files:
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(base_dir, dst))
        else:
            print(f"Warning: {src} not found.")
            
    # 3. Copy SHAP
    shap_dir = "d:/cardiogaurd/ai/results/shap"
    if os.path.exists(shap_dir):
        shutil.copytree(shap_dir, os.path.join(base_dir, "shap"), dirs_exist_ok=True)
        
    print(f"Experiment frozen to {base_dir}")

if __name__ == "__main__":
    freeze_experiment()

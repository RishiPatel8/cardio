import os
import json
import numpy as np
import pandas as pd
import joblib
from datetime import datetime

import sys
sys.path.append('d:/cardiogaurd')
from ai.config.experiment_config import config
from ai.preprocessing.pipeline import PreprocessingPipeline

def generate_shap_bg():
    print("Loading scaler...")
    scaler_path = "d:/cardiogaurd/ai/artifacts/models/scaler.pkl"
    if not os.path.exists(scaler_path):
        print("Error: scaler not found.")
        return
    
    pipeline = PreprocessingPipeline(sampling_rate=125, window_size=187)
    pipeline.scaler = joblib.load(scaler_path)
    pipeline.is_fitted = True
    
    print("Loading subset of training data to match existing model's 5% subset...")
    train_df = pd.read_csv("d:/cardiogaurd/ai/datasets/mitbih_train.csv", header=None)
    
    # Same subsample logic used during the original 5% training
    subsample_ratio = 0.05
    train_df = train_df.groupby(187, group_keys=False).apply(lambda x: x.sample(frac=subsample_ratio, random_state=42))
    
    X_train_full = train_df.iloc[:, :-1].values
    
    print("Preprocessing...")
    X_processed = pipeline.process_inference_data(X_train_full)
    
    # Reshape for CNN+LSTM: (samples, time_steps, features)
    X_dl = X_processed.reshape((X_processed.shape[0], X_processed.shape[1], 1))
    
    print("Sampling 100 background samples...")
    np.random.seed(42)
    bg_indices = np.random.choice(X_dl.shape[0], 100, replace=False)
    shap_bg = X_dl[bg_indices]
    
    bg_path = "d:/cardiogaurd/ai/artifacts/models/shap_background.npy"
    np.save(bg_path, shap_bg)
    print(f"Saved SHAP background to {bg_path}")
    
    # Read existing comparison for metrics
    comp_path = "d:/cardiogaurd/ai/results/experiments/experiment_2026_08_25_151056/comparison.json"
    metrics = {}
    if os.path.exists(comp_path):
        with open(comp_path, 'r') as f:
            metrics = json.load(f).get("CNN_LSTM", {})
            
    # Write registry
    registry = {
        "active_model": "cnn_lstm",
        "version": "1.0.0",
        "artifact_path": "d:/cardiogaurd/ai/artifacts/models/cnn_lstm/cnn_lstm.h5",
        "scaler_path": scaler_path,
        "shap_background_path": bg_path,
        "training_timestamp": "2026-08-25T15:10:56Z",
        "dataset": {
            "source": "shayanfazeli/heartbeat",
            "name": "MIT-BIH Arrhythmia Database",
            "scope": "5% subset"
        },
        "preprocessing": {
            "version": "1.0",
            "features": 186
        },
        "metrics": metrics
    }
    
    registry_path = "d:/cardiogaurd/ai/config/registry.json"
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=4)
    print("Updated registry.json")

if __name__ == "__main__":
    generate_shap_bg()

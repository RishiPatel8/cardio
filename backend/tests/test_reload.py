import os
import joblib
import pandas as pd
import numpy as np

def test_reload():
    test_csv = "d:/cardiogaurd/ai/datasets/mitbih_test.csv"
    test_df = pd.read_csv(test_csv, header=None)
    
    # Take one sample and strictly enforce 186 features to match the scaler
    sample_raw = test_df.iloc[0:1, :186].values
    true_label = test_df.iloc[0, -1]
    
    print(f"Testing reloading for 1 sample (True Label: {true_label})...")
    
    # 1. Load preprocessing scaler
    scaler_path = "d:/cardiogaurd/ai/artifacts/models/scaler.pkl"
    if not os.path.exists(scaler_path):
        print(f"FAIL: Scaler missing at {scaler_path}")
        return
        
    scaler = joblib.load(scaler_path)
    
    # Simulate the pipeline transformations
    # Missing values
    sample_clean = pd.DataFrame(sample_raw).ffill().bfill().values
    
    # For a quick test we can directly use scaler.transform
    # In a full inference we'd also run bandpass/notch but here we just prove reloading works.
    try:
        sample_scaled = scaler.transform(sample_clean)
        print("PASS: Scaler reloaded and transformed data successfully.")
    except Exception as e:
        print(f"FAIL: Scaler transformation failed: {e}")
        return
        
    # 2. Test each baseline model
    baselines = ["svm", "random_forest", "decision_tree"]
    
    for b in baselines:
        model_path = f"d:/cardiogaurd/ai/artifacts/models/{b}/model.pkl"
        if os.path.exists(model_path):
            model = joblib.load(model_path)
            try:
                pred = model.predict(sample_scaled)
                print(f"PASS: {b} reloaded and predicted -> {pred[0]}")
            except Exception as e:
                print(f"FAIL: {b} prediction failed -> {e}")
        else:
            print(f"FAIL: {b} artifact missing.")

if __name__ == "__main__":
    test_reload()

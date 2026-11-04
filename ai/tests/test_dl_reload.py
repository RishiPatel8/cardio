import os
import joblib
import pandas as pd
import numpy as np

def test_dl_reload():
    test_csv = "d:/cardiogaurd/ai/datasets/mitbih_test.csv"
    test_df = pd.read_csv(test_csv, header=None)
    
    # Take one sample
    sample_raw = test_df.iloc[0:1, :186].values
    true_label = test_df.iloc[0, -1]
    
    print(f"Testing DL reloading for 1 sample (True Label: {true_label})...")
    
    scaler_path = "d:/cardiogaurd/ai/artifacts/models/scaler.pkl"
    if not os.path.exists(scaler_path):
        print(f"FAIL: Scaler missing at {scaler_path}")
        return
        
    scaler = joblib.load(scaler_path)
    sample_clean = pd.DataFrame(sample_raw).ffill().bfill().values
    sample_scaled = scaler.transform(sample_clean)
    
    import tensorflow as tf
    model_path = "d:/cardiogaurd/ai/artifacts/models/cnn_lstm/cnn_lstm.h5"
    if not os.path.exists(model_path):
        print(f"FAIL: Model missing at {model_path}")
        return
        
    model = tf.keras.models.load_model(model_path)
    
    # DL Models expect (samples, time_steps, features)
    sample_dl = sample_scaled.reshape(1, sample_scaled.shape[1], 1)
    
    try:
        pred_prob = model.predict(sample_dl, verbose=0)
        pred = (pred_prob > 0.5).astype(int)
        print(f"PASS: CNN+LSTM reloaded and predicted -> {pred[0][0]} (Prob: {pred_prob[0][0]:.4f})")
    except Exception as e:
        print(f"FAIL: CNN+LSTM prediction failed -> {e}")

if __name__ == "__main__":
    test_dl_reload()

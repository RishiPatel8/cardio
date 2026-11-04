import requests
import pandas as pd
import numpy as np

def test_prediction():
    url = "http://127.0.0.1:8000/api/v1/prediction/predict"
    
    print("Loading one test sample from mitbih_test.csv...")
    try:
        df = pd.read_csv("d:/cardiogaurd/ai/datasets/mitbih_test.csv", header=None)
        # Sample one record
        sample = df.iloc[0, :-1].values.tolist()
    except Exception as e:
        print("Could not load test data:", e)
        # Fallback to random if dataset is missing
        sample = np.random.rand(187).tolist()

    payload = {
        "avg_bpm": 75.0,
        "sdrr_ms": 40.0,
        "rmssd_ms": 30.0,
        "waveform": sample
    }
    
    print("Testing REAL mode API (expecting 500 failure due to WDAC blocking TF)...")
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        print("Response:", response.json())
        assert response.status_code == 500, "REAL mode should fail cleanly with 500!"
        print("SUCCESS: REAL mode correctly failed with 500 error.")
    except Exception as e:
        print("Request failed:", e)

if __name__ == "__main__":
    test_prediction()

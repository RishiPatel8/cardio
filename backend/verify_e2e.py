import requests
import json
import os
import numpy as np
import tempfile
import time

BASE_URL = "http://localhost:8000/api/v1"

def create_dummy_csv():
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, 'w') as f:
        # Create 1000 lines of dummy ECG data
        for _ in range(1000):
            f.write(f"{np.random.randn()}\n")
    return path

def run_prediction(model_id, csv_path):
    print(f"\n==================================================")
    print(f"TESTING MODEL: {model_id}")
    print(f"==================================================")
    
    url = f"{BASE_URL}/predictions/physionet"
    if model_id == "compare":
        url = f"{BASE_URL}/predictions/compare"
        
    with open(csv_path, 'rb') as f:
        files = {'files': ('dummy.csv', f, 'text/csv')}
        data = {'age': '45', 'sex': '1'}
        
        if model_id == "compare":
            # Fetch available models first
            res_models = requests.get(f"{BASE_URL}/models")
            if res_models.status_code == 200:
                models = res_models.json()
                model_ids = ",".join([m["id"] for m in models])
                data["model_ids"] = model_ids
                print(f"Comparing models: {model_ids}")
        else:
            if model_id != "default":
                data["model_id"] = model_id
                
        start_time = time.time()
        response = requests.post(url, files=files, data=data)
        latency = time.time() - start_time
        
        print(f"HTTP Status: {response.status_code}")
        print(f"Latency: {latency:.2f}s")
        
        try:
            resp_json = response.json()
            print("Response:", json.dumps(resp_json, indent=2))
        except Exception as e:
            print("Failed to parse JSON response:", e)
            print("Raw text:", response.text)

if __name__ == "__main__":
    # Get available models
    try:
        models = requests.get(f"{BASE_URL}/models").json()
        model_ids = [m["id"] for m in models]
        print(f"FOUND {len(model_ids)} REGISTERED MODELS: {model_ids}")
    except Exception as e:
        print("Failed to fetch models:", e)
        exit(1)
        
    csv_path = create_dummy_csv()
    
    # 1. Test each model individually
    for mid in model_ids:
        run_prediction(mid, csv_path)
        
    # 2. Test compare all
    run_prediction("compare", csv_path)
    
    os.remove(csv_path)

import requests
import json

def main():
    raw_signal = []
    with open("../docs/test_ecg.csv", "r", encoding="utf-16le") as f:
        lines = f.readlines()
        for line in lines:
            for val in line.split(','):
                try:
                    raw_signal.append(float(val.strip()))
                except:
                    pass

    print(f"Loaded {len(raw_signal)} values.")

    payload = {
        "telemetry_id": None,
        "avg_bpm": 75.0,
        "sdrr_ms": 45.0,
        "rmssd_ms": 35.0,
        "raw_ecg": raw_signal,
        "fs": 100.0
    }

    headers = {
        "Authorization": "Bearer mock_firebase_mockuser"
    }
    
    try:
        response = requests.post("http://localhost:8000/api/v1/prediction", json=payload, headers=headers)
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)
    except Exception as e:
        print("Failed to query:", e)

if __name__ == "__main__":
    main()

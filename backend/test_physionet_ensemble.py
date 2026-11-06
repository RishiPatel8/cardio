import requests
import json

def test_physionet_ensemble():
    url = "http://localhost:8000/api/v1/predictions/physionet"
    files = [
        ("files", ("100.dat", open("G:/cardio/100.dat", "rb"), "application/octet-stream")),
        ("files", ("100.hea", open("G:/cardio/100.hea", "rb"), "application/octet-stream")),
    ]
    data = {
        "model_id": "v9_ensemble",
        "age": "69.0",
        "sex": "0"
    }
    
    print("Uploading 100.dat + 100.hea with model_id=v9_ensemble...")
    res = requests.post(url, files=files, data=data)
    print(f"Status Code: {res.status_code}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    
    body = res.json()
    print("=== PHYSIONET ENSEMBLE RESPONSE ===")
    print(f"Result Type: {body.get('resultType')}")
    print(f"Confidence: {body.get('confidence')}%")
    print(f"Model Version: {body.get('modelVersion')}")
    print(f"Contributing Models: {body.get('contributing_models_count')} active")
    print(f"Excluded Models: {len(body.get('excluded_models', []))}")
    print(f"Probability Vector: {body.get('probability_vector')}")
    if body.get('agreement_analysis'):
        print(f"Model Agreement: {body['agreement_analysis'].get('agreement_percentage')}%")
        print(f"Agreeing Models: {body['agreement_analysis'].get('agreeing_models')}")
        print(f"Disagreeing Models: {body['agreement_analysis'].get('disagreeing_models')}")
    print("SUCCESS: PhysioNet multi-file upload with v9_ensemble verified!")

if __name__ == "__main__":
    test_physionet_ensemble()

import asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import sys
import os

sys.path.append(r'g:/cardio\backend')

# Add missing schemas for SQLAlchemy
from app.models.prediction import Prediction
from app.core.config import settings
from pydantic import BaseModel

async def run_validation():
    print("\n--- CARDIOGUARD VALIDATION SCRIPT ---\n")
    
    # 1. API AUTHENTICATION & UPLOAD
    print("1. Testing API Authentication & Upload...")
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # We need a mock token or real token. Since Offline mode is active, any bearer token works.
        headers = {"Authorization": "Bearer mock_firebase_123", "X-Firebase-AppCheck": "mock_app_check_token_123"}
        
        # Unauthorized check
        resp = await client.get("/api/v1/users/me")
        print(f"Missing Auth -> {resp.status_code} (Expect 401)")
        assert resp.status_code in [401, 403], "Auth enforcement failed!"
        
        # Authorized check
        resp = await client.get("/api/v1/users/me", headers=headers)
        print(f"Valid Auth -> {resp.status_code} (Expect 200)")
        assert resp.status_code == 200, "Auth enforcement failed!"
        user_id = resp.json().get("id")
        
        # Malformed CSV check
        bad_csv = b"random,string,not,a,csv\n1,2,3,4,5"
        resp = await client.post(
            "/api/v1/predictions/physionet",
            headers=headers,
            files={"file": ("bad.csv", bad_csv, "text/csv")},
            data={"fs": 100}
        )
        print(f"Malformed ECG -> {resp.status_code} (Expect 4xx)")
        assert resp.status_code in [400, 422], "Malformed ECG not rejected!"
        
        # Real ECG Upload
        # We will use mitbih_test.csv from ai/datasets
        dataset_path = r'g:/cardio\ai\datasets\mitbih_test.csv'
        print(f"Uploading Real ECG: {dataset_path}")
        
        with open(dataset_path, "rb") as f:
            resp = await client.post(
                "/api/v1/predictions/physionet",
                headers=headers,
                files={"file": ("mitbih_test.csv", f, "text/csv")},
                data={"fs": 100}
            )
            
        print(f"Real ECG Upload -> {resp.status_code}")
        assert resp.status_code == 201, f"Failed: {resp.text}"
        data = resp.json()
        print("API Response Structure:")
        print(f" - classification: {data.get('classification')}")
        print(f" - confidence_score: {data.get('confidence_score')}")
        print(f" - probability_vector: {data.get('probability_vector')}")
        print(f" - model_version: {data.get('model_version')}")
        print(f" - raw_ecg length: {len(data.get('raw_ecg', []))}")
        print(f" - explainable_insights length: {len(data.get('explainable_insights', []))}")
        
        prediction_id = data.get("id")
        
    print("\n2. Testing Database Persistence...")
    # 2. DATABASE VERIFICATION
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        query = text("SELECT * FROM predictions WHERE id = :id")
        result = await session.execute(query, {"id": prediction_id})
        db_record = result.mappings().first()
        
        assert db_record is not None, "Record not found in DB!"
        print("Database Record Structure:")
        print(f" - id: {db_record['id']}")
        print(f" - classification: {db_record['classification']}")
        print(f" - confidence: {db_record['confidence']}")
        print(f" - probability_vector: {db_record['probability_vector']}")
        print(f" - model_version: {db_record['model_version']}")
        print(f" - inference_time_ms: {db_record['inference_time_ms']}")
        
        # Verify alignment
        assert db_record['classification'] == data['classification'], "Classification mismatch"
        # Database might store confidence rounded or slightly different depending on float, so just approximate
        assert abs(db_record['confidence'] - data['confidence_score']) < 0.001, "Confidence mismatch"
        assert db_record['model_version'] == data['model_version'], "Model version mismatch"

    print("\nALL BACKEND VALIDATIONS PASSED.")

if __name__ == "__main__":
    asyncio.run(run_validation())


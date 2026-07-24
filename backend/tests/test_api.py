import pytest
import uuid
import os
from httpx import AsyncClient
from app.models.wearable_data import WearableData
from app.models.prediction import Prediction
from app.models.notification import Notification
from app.models.report import Report
from app.repositories.wearable_data import WearableDataRepository
from app.repositories.prediction import PredictionRepository
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_system_health(client: AsyncClient):
    response = await client.get("/api/v1/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["cache"] == "connected"

@pytest.mark.asyncio
async def test_get_me_profile(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test_user@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_sync_wearable_metrics(client: AsyncClient):
    payload = {
        "source": "google_fit",
        "avg_bpm": 76.5,
        "sdrr_ms": 48.0,
        "rmssd_ms": 32.5,
        "timeseries_data": [
            {"time_sec": 10.0, "rr_interval_ms": 800.0, "bpm": 75}
        ]
    }
    response = await client.post("/api/v1/wearables/sync", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "google_fit"
    assert data["avg_bpm"] == 76.5

@pytest.mark.asyncio
async def test_sync_wearable_metrics_deduplication(client: AsyncClient):
    payload = {
        "source": "google_fit",
        "avg_bpm": 76.5,
        "sdrr_ms": 48.0,
        "rmssd_ms": 32.5,
        "timeseries_data": [
            {"time_sec": 10.0, "rr_interval_ms": 800.0, "bpm": 75}
        ]
    }
    # First sync
    res_1 = await client.post("/api/v1/wearables/sync", json=payload)
    assert res_1.status_code == 200
    
    # Second sync (duplicate payload should process gracefully)
    res_2 = await client.post("/api/v1/wearables/sync", json=payload)
    assert res_2.status_code == 200

@pytest.mark.asyncio
async def test_run_ai_prediction(client: AsyncClient, db_session: AsyncSession):
    # Pre-seed a wearable data telemetry record
    user_id = uuid.UUID("4c02283e-a89e-4ff6-8c46-9c46e3ea86bf")
    telemetry = WearableData(
        id=uuid.uuid4(),
        user_id=user_id,
        source="google_fit",
        avg_bpm=74.0,
        sdrr_ms=45.5,
        rmssd_ms=31.0
    )
    db_session.add(telemetry)
    await db_session.commit()
    
    payload = {
        "telemetry_id": str(telemetry.id),
        "avg_bpm": 74.0,
        "sdrr_ms": 45.5,
        "rmssd_ms": 31.0
    }
    response = await client.post("/api/v1/prediction", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "classification" in data
    assert "confidence_score" in data
    assert len(data["explainable_insights"]) > 0

@pytest.mark.asyncio
async def test_prediction_triggers_notification(client: AsyncClient, db_session: AsyncSession):
    # Test that high risk (anomaly) predictions trigger automatic notification inserts
    payload = {
        "avg_bpm": 110.0,  # Elevated HR
        "sdrr_ms": 15.0,   # Critically low HRV -> driving anomaly classification
        "rmssd_ms": 10.0
    }
    response = await client.post("/api/v1/prediction", json=payload)
    assert response.status_code == 200
    
    # Query database notifications for the test user
    from sqlalchemy.future import select
    user_id = uuid.UUID("4c02283e-a89e-4ff6-8c46-9c46e3ea86bf")
    result = await db_session.execute(
        select(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc())
    )
    notifications = result.scalars().all()
    assert len(notifications) > 0
    # The notification should notify the user of an anomaly
    assert "abnormal" in notifications[0].message.lower() or "alert" in notifications[0].title.lower()

@pytest.mark.asyncio
async def test_daily_analytics(client: AsyncClient, db_session: AsyncSession):
    # Seed historical telemetry logs to aggregate
    user_id = uuid.UUID("4c02283e-a89e-4ff6-8c46-9c46e3ea86bf")
    telemetry_1 = WearableData(user_id=user_id, source="google_fit", avg_bpm=72.0, sdrr_ms=45.0, rmssd_ms=30.0)
    telemetry_2 = WearableData(user_id=user_id, source="google_fit", avg_bpm=80.0, sdrr_ms=50.0, rmssd_ms=34.0)
    db_session.add_all([telemetry_1, telemetry_2])
    await db_session.commit()
    
    response = await client.get("/api/v1/analytics/daily")
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "daily"
    assert "average_heart_rate" in data
    # Averaged heart rate should be roughly 76
    assert 70.0 <= data["average_heart_rate"] <= 80.0

@pytest.mark.asyncio
async def test_pdf_report_generation_and_download(client: AsyncClient, db_session: AsyncSession):
    user_id = uuid.UUID("4c02283e-a89e-4ff6-8c46-9c46e3ea86bf")
    # Seed a prediction to base the report on
    pred = Prediction(
        id=uuid.uuid4(),
        user_id=user_id,
        classification="Normal",
        confidence_score=98.2,
        model_version="ensemble-rf",
        explainable_insights=["Perfect rhythm", "High autonomic tone"]
    )
    db_session.add(pred)
    await db_session.commit()
    
    payload = {
        "title": "Monthly Diagnostic Health Summary",
        "prediction_id": str(pred.id)
    }
    
    # 1. Generate Report
    res_gen = await client.post("/api/v1/reports/generate", json=payload)
    assert res_gen.status_code == 201
    data = res_gen.json()
    assert data["title"] == "Monthly Diagnostic Health Summary"
    assert "report_url" in data
    
    # Resolve report filename from URL
    filename = data["report_url"].split("/")[-1]
    
    # 2. Download Report File
    res_dl = await client.get(f"/api/v1/reports/download/{filename}")
    assert res_dl.status_code == 200
    assert res_dl.headers["content-type"] == "application/pdf"
    assert len(res_dl.content) > 0

@pytest.mark.asyncio
async def test_error_recovery_invalid_token(client: AsyncClient):
    # Remove authentication override to test token checks
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]
        
    headers = {"Authorization": "Bearer invalid_expired_jwt_signature_xyz"}
    response = await client.get("/api/v1/users/me", headers=headers)
    # Authentication check should reject the request with 401 Unauthorized
    assert response.status_code in [401, 403]

@pytest.mark.asyncio
async def test_error_recovery_missing_payload(client: AsyncClient):
    response = await client.post("/api/v1/prediction", json={})
    # Validation error (missing fields in body) should return 422 Unprocessable Entity
    assert response.status_code == 422

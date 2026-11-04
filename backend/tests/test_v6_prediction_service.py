import pytest
import numpy as np
from unittest.mock import AsyncMock, patch, MagicMock
from app.schemas.prediction import PredictionRequest
from app.services.prediction import PredictionService
from fastapi import HTTPException
import uuid

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    return db

@pytest.fixture
def prediction_service(mock_db):
    return PredictionService(db=mock_db)

@pytest.mark.asyncio
async def test_prediction_service_valid_ecg(prediction_service):
    # Create a dummy 10-second ECG signal at 100Hz
    # 1000 samples, normal range (sine wave to pass SQI zero-crossing checks)
    raw_ecg = np.sin(np.linspace(0, 10 * 2 * np.pi, 1000)).tolist()
    
    request = PredictionRequest(
        telemetry_id=uuid.uuid4(),
        avg_bpm=75.0,
        sdrr_ms=45.0,
        rmssd_ms=35.0,
        raw_ecg=raw_ecg,
        fs=100.0
    )
    
    # Needs to bypass or use the loaded model. Since it's imported globally, it should run the actual model
    # if it's available. To avoid slow tests or missing model artifacts in CI, we mock the model predict if needed.
    # But since this is a local integration test, we can actually let it run the real model.
    try:
        prediction = await prediction_service.generate_ai_prediction(uuid.uuid4(), request)
        assert prediction is not None
        assert prediction.classification in ["Normal", "AFIB", "Conduction Block", "Other Arrhythmia"]
        assert 0.0 <= prediction.confidence_score <= 100.0
        assert len(prediction.probability_vector) == 4
        assert np.isclose(sum(prediction.probability_vector), 1.0, atol=1e-2)
        assert "MODEL PREDICTION: Normal" in prediction.explainable_insights[0]
    except Exception as e:
        pytest.fail(f"Prediction failed with exception: {e}")

@pytest.mark.asyncio
async def test_prediction_service_sqi_flatline(prediction_service):
    # Flatline signal should fail SQI
    raw_ecg = [0.0] * 1000
    
    request = PredictionRequest(
        telemetry_id=uuid.uuid4(),
        raw_ecg=raw_ecg,
        fs=100.0
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await prediction_service.generate_ai_prediction(uuid.uuid4(), request)
        
    assert exc_info.value.status_code == 400
    assert "Signal Quality Invalid" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_prediction_service_short_ecg(prediction_service):
    raw_ecg = [0.5] * 50 # Too short
    
    request = PredictionRequest(
        telemetry_id=uuid.uuid4(),
        raw_ecg=raw_ecg,
        fs=100.0
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await prediction_service.generate_ai_prediction(uuid.uuid4(), request)
        
    assert exc_info.value.status_code == 400
    assert "too short" in str(exc_info.value.detail)

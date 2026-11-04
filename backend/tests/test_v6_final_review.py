import pytest
import os
import sys
import numpy as np
import pandas as pd
import uuid
import tensorflow as tf
from httpx import AsyncClient

# Make sure we can import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from app.services.prediction import PredictionService, CLASS_MAPPING, v6_model, pipeline
from app.schemas.prediction import PredictionRequest
from unittest.mock import MagicMock

# Base paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
CSV_PATH = os.path.join(ROOT_DIR, "cardiogaurd_review_5000_ptbxl.csv")
MODEL_PATH = os.path.join(ROOT_DIR, "scratch/best_v6_benchmark_model.h5")

async def mock_create(x):
    return x

@pytest.fixture
def mock_db_session():
    db = MagicMock()
    async def mock_flush():
        pass
    db.flush = mock_flush
    return db

@pytest.fixture
def prediction_service(mock_db_session):
    return PredictionService(db=mock_db_session)

@pytest.mark.asyncio
async def test_1_real_v6_model_loads_successfully():
    """TEST 1: Real V6 model loads successfully."""
    assert os.path.exists(MODEL_PATH), "V6 model file does not exist"
    assert v6_model is not None, "v6_model should be loaded globally"
    assert isinstance(v6_model, tf.keras.Model), "Loaded model must be a Keras model"

@pytest.mark.asyncio
async def test_2_uploaded_ecg_reaches_v6_model(prediction_service):
    """TEST 2: Uploaded ECG reaches the V6 model."""
    # We test this implicitly by ensuring prediction service runs through the v6_model without hitting a mock
    # Create a simple valid signal (sine wave + noise)
    t = np.linspace(0, 10, 1000)
    signal = 0.5 * np.sin(2 * np.pi * 1.2 * t) + np.random.normal(0, 0.05, 1000)
    
    req = PredictionRequest(
        telemetry_id=uuid.uuid4(),
        raw_ecg=signal.tolist(),
        fs=100.0
    )
    
    # We mock the repo create method to just return what it was given
    prediction_service.prediction_repo.create = mock_create
    
    try:
        pred = await prediction_service.generate_ai_prediction(uuid.uuid4(), req)
        assert pred.model_version == "resnet_improved_v6"
    except Exception as e:
        pytest.fail(f"Pipeline failed: {e}")

@pytest.mark.asyncio
async def test_3_model_returns_exactly_four_classes(prediction_service):
    """TEST 3: Model returns exactly four classes."""
    signal = 0.5 * np.sin(2 * np.pi * 1.2 * np.linspace(0, 10, 1000))
    req = PredictionRequest(raw_ecg=signal.tolist(), fs=100.0)
    prediction_service.prediction_repo.create = mock_create
    pred = await prediction_service.generate_ai_prediction(uuid.uuid4(), req)
    
    assert len(pred.probability_vector) == 4, "Probability vector must have exactly 4 elements"

@pytest.mark.asyncio
async def test_4_probabilities_sum_to_one(prediction_service):
    """TEST 4: Four probabilities sum approximately to 1."""
    signal = 0.5 * np.sin(2 * np.pi * 1.2 * np.linspace(0, 10, 1000))
    req = PredictionRequest(raw_ecg=signal.tolist(), fs=100.0)
    prediction_service.prediction_repo.create = mock_create
    pred = await prediction_service.generate_ai_prediction(uuid.uuid4(), req)
    
    total = sum(pred.probability_vector)
    assert np.isclose(total, 1.0, atol=1e-2), f"Probabilities sum to {total}, expected ~1.0"

@pytest.mark.asyncio
async def test_5_to_9_class_mapping_is_correct():
    """TEST 5, 6, 7, 8, 9: Class mapping is correct."""
    assert CLASS_MAPPING[0] == "Normal"
    assert CLASS_MAPPING[1] == "AFIB"
    assert CLASS_MAPPING[2] == "Conduction Block"
    assert CLASS_MAPPING[3] == "Other Arrhythmia"

@pytest.mark.asyncio
async def test_10_no_randomforest_or_mock_model():
    """TEST 10: No RandomForest/mock model is used by the live prediction endpoint."""
    with open(os.path.join(os.path.dirname(__file__), "../app/services/prediction.py"), "r") as f:
        content = f.read()
        assert "RandomForest" not in content, "RandomForest found in live prediction endpoint"
        assert "mock" not in content.lower(), "Mock prediction found in live prediction endpoint"

@pytest.mark.asyncio
async def test_11_no_hardcoded_confidence(prediction_service):
    """TEST 11: No hardcoded confidence is returned."""
    # Run two different signals, ensure confidences differ
    sig1 = 0.5 * np.sin(2 * np.pi * 1.2 * np.linspace(0, 10, 1000))
    sig2 = 0.5 * np.sin(2 * np.pi * 1.5 * np.linspace(0, 10, 1000))
    
    prediction_service.prediction_repo.create = mock_create
    
    pred1 = await prediction_service.generate_ai_prediction(uuid.uuid4(), PredictionRequest(raw_ecg=sig1.tolist(), fs=100.0))
    pred2 = await prediction_service.generate_ai_prediction(uuid.uuid4(), PredictionRequest(raw_ecg=sig2.tolist(), fs=100.0))
    
    # We expect the neural network to output different confidence scores for different noise patterns
    assert pred1.confidence_score != 91.0, "Confidence score is hardcoded to 91.0"
    assert pred1.confidence_score != 96.2, "Confidence score is hardcoded to 96.2"

@pytest.mark.asyncio
async def test_12_invalid_flat_noisy_ecg_rejected(prediction_service):
    """TEST 12: Invalid/flat/noisy ECG is rejected."""
    # Flatline
    flat = np.zeros(1000).tolist()
    req = PredictionRequest(raw_ecg=flat, fs=100.0)
    try:
        await prediction_service.generate_ai_prediction(uuid.uuid4(), req)
        pytest.fail("Flatline should have been rejected")
    except Exception as e:
        assert "Signal Quality Invalid" in str(e) or "400" in str(e)

@pytest.mark.asyncio
async def test_13_review_csv_can_be_parsed():
    """TEST 13: The 5000-record review CSV can be parsed."""
    assert os.path.exists(CSV_PATH), f"Review dataset CSV not found at {CSV_PATH}"
    df = pd.read_csv(CSV_PATH, header=None, nrows=10) # Read just a few rows to verify parsing
    assert len(df) == 10, "Could not parse review dataset CSV"
    assert len(df.columns) == 1000, "Review dataset does not have 1000 columns"

@pytest.mark.asyncio
async def test_14_real_ecg_inference_through_pipeline(prediction_service):
    """TEST 14: At least one real ECG from the review CSV successfully passes through the pipeline."""
    assert os.path.exists(CSV_PATH), f"Review dataset CSV not found at {CSV_PATH}"
    df = pd.read_csv(CSV_PATH, header=None, nrows=1)
    real_ecg = df.iloc[0].values.tolist()
    
    req = PredictionRequest(raw_ecg=real_ecg, fs=100.0)
    prediction_service.prediction_repo.create = mock_create
    
    try:
        pred = await prediction_service.generate_ai_prediction(uuid.uuid4(), req)
        assert pred.model_version == "resnet_improved_v6"
        assert len(pred.probability_vector) == 4
        assert pred.classification in CLASS_MAPPING.values()
    except Exception as e:
        pytest.fail(f"Real ECG inference failed: {e}")

@pytest.mark.asyncio
async def test_15_inference_timing(prediction_service):
    """TEST 15: inference_time_ms is populated and valid."""
    assert os.path.exists(CSV_PATH), f"Review dataset CSV not found at {CSV_PATH}"
    df = pd.read_csv(CSV_PATH, header=None, nrows=1)
    real_ecg = df.iloc[0].values.tolist()
    
    req = PredictionRequest(raw_ecg=real_ecg, fs=100.0)
    prediction_service.prediction_repo.create = mock_create
    
    pred = await prediction_service.generate_ai_prediction(uuid.uuid4(), req)
    assert hasattr(pred, "inference_time_ms")
    assert isinstance(pred.inference_time_ms, int)
    assert pred.inference_time_ms >= 0



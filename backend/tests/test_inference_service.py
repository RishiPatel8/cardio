import pytest
import os
from app.services.inference_service import InferenceService

@pytest.fixture
def inference_service():
    from app.services.shap_service import shap_service_instance
    import app.services.shap_service
    app.services.shap_service.shap_service_instance = None
    
    # Force demo mode for deterministic testing without TF overhead
    os.environ["PREDICTION_MODE"] = "demo"
    return InferenceService()

@pytest.mark.skipif(os.environ.get("PREDICTION_MODE", "demo").lower() == "real", reason="Demo inference disabled in real mode")
def test_inference_service_initialization(inference_service):
    # Verify it initializes in demo mode when env var is set
    assert inference_service.mode == "demo"
    assert inference_service.model_version in ["demo-v1", "1.0.0", "cnn_lstm_v2"]

@pytest.mark.skipif(os.environ.get("PREDICTION_MODE", "demo").lower() == "real", reason="Demo inference disabled in real mode")
def test_inference_service_demo_prediction_normal(inference_service):
    payload = {
        "sdrr_ms": 50,
        "rmssd_ms": 30
    }
    result = inference_service.run_inference(payload)
    
    assert result["mode"] == "DEMO"
    assert result["is_anomaly"] is False
    assert result["classification"] == "Normal Sinus Rhythm"
    assert result["confidence_score"] > 90.0

@pytest.mark.skipif(os.environ.get("PREDICTION_MODE", "demo").lower() == "real", reason="Demo inference disabled in real mode")
def test_inference_service_demo_prediction_anomaly(inference_service):
    payload = {
        "sdrr_ms": 95, # Trigger anomaly
        "rmssd_ms": 85  # Trigger anomaly
    }
    result = inference_service.run_inference(payload)
    
    assert result["is_anomaly"] is True
    assert result["classification"] in ["Atrial Fibrillation"]
    assert result["risk_tier"] == "high"

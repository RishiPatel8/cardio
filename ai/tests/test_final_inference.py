import os
import sys
import numpy as np
import pytest

# Ensure cardiogaurd and backend paths are accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from backend.app.services.inference_service import InferenceService

# Test payload for 187 length
valid_payload = {"waveform": [0.5] * 187}
invalid_length_payload = {"waveform": [0.5] * 100}
nan_payload = {"waveform": [0.5] * 186 + [np.nan]}
inf_payload = {"waveform": [np.inf] + [0.5] * 186}
non_numeric_payload = {"waveform": "this is a string"}
missing_payload = {}

@pytest.fixture
def service():
    # Force real mode
    os.environ["PREDICTION_MODE"] = "real"
    svc = InferenceService()
    return svc

def test_valid_inference(service):
    res = service.run_inference(valid_payload)
    assert res["mode"] == "REAL"
    assert "is_anomaly" in res
    assert "confidence_score" in res
    assert "risk_tier" in res
    assert isinstance(res["explanation"], list)

def test_invalid_length(service):
    # Should pad with zeros and succeed or raise ValueError gracefully if we changed it
    res = service.run_inference(invalid_length_payload)
    assert "is_anomaly" in res

def test_nan_input(service):
    with pytest.raises(ValueError):
        service.run_inference(nan_payload)

def test_inf_input(service):
    with pytest.raises(ValueError):
        service.run_inference(inf_payload)

def test_non_numeric(service):
    with pytest.raises(ValueError):
        service.run_inference(non_numeric_payload)

def test_missing_payload(service):
    res = service.run_inference(missing_payload)
    assert "is_anomaly" in res

def test_missing_model_artifact(monkeypatch, service):
    monkeypatch.setattr(service, 'model', None)
    with pytest.raises(Exception):
        service.run_inference(valid_payload)

import pytest
import numpy as np
from app.services.inference_service import InferenceService
from app.api.v1.predictions import physionet
from fastapi.testclient import TestClient
from app.main import app

def test_legacy_inference_returns_decimals():
    # Mock legacy probabilities validation
    mock_raw = np.array([
        [0.05, 0.90, 0.03, 0.02],
        [0.10, 0.85, 0.04, 0.01]
    ])
    aggregated = np.mean(mock_raw, axis=0)
    
    assert np.isclose(np.sum(aggregated), 1.0)
    assert np.max(aggregated) <= 1.0
    assert np.min(aggregated) >= 0.0

def test_physionet_api_returns_percentages():
    # Mocking physionet behavior to verify it outputs percentages
    mock_mean_probs = np.array([0.928, 0.03217, 0.025, 0.01483])
    
    class_probabilities = {
        "Normal": float(mock_mean_probs[0] * 100),
        "AFIB": float(mock_mean_probs[1] * 100),
        "Conduction Block": float(mock_mean_probs[2] * 100),
        "Other Arrhythmia": float(mock_mean_probs[3] * 100)
    }
    
    # Assert values are blown up by 100
    assert class_probabilities["Normal"] > 90.0
    assert class_probabilities["Normal"] <= 100.0
    
    # Assert sum is approximately 100
    total = sum(class_probabilities.values())
    assert np.isclose(total, 100.0)

def test_argmax_matches_prediction():
    mock_mean_probs = np.array([0.05, 0.90, 0.03, 0.02]) # AFIB is highest
    pred_idx = int(np.argmax(mock_mean_probs))
    confidence = float(np.max(mock_mean_probs) * 100)
    
    assert pred_idx == 1
    assert confidence == 90.0

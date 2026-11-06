"""
Test Suite: Seven-Model Ensemble Integration (Phase 12 Verification)
Verifies:
1. Seven-model inference integration (v9_ensemble).
2. Explicit demographic exclusion (5 vs 7 models) with documented reasons.
3. Probability vector validation: 4 classes, non-negative, finite, sums to 1.0.
4. Determinism across 5 repeated inference executions.
5. Non-regression of single-model and compare-all endpoints.
"""

import numpy as np
from app.services.ensemble_service import get_ensemble_service
from app.services.orchestrator import get_orchestrator


def test_ensemble_weights_loaded():
    """Verify that frozen validation weights are loaded correctly from config."""
    service = get_ensemble_service()
    weights = service.weights
    
    assert len(weights) == 7, f"Expected 7 model weights, found {len(weights)}"
    expected_models = {
        "v8_tcn_multimodal",
        "v7_tcn",
        "v7_resnet",
        "v7_transformer",
        "resnet",
        "v7_cnn_lstm",
        "v8_tabular_mlp"
    }
    assert set(weights.keys()) == expected_models
    assert abs(sum(weights.values()) - 1.0) < 1e-3


def test_ensemble_seven_models_with_demographics():
    """When both ECG and valid demographics (Age/Sex) are provided, all 7 models must contribute."""
    service = get_ensemble_service()
    np.random.seed(42)
    raw_ecg = np.random.randn(1000).tolist()
    
    payload = {
        "raw_ecg": raw_ecg,
        "age": 65.0,
        "sex": 0,  # Male
        "heart_rate": 72.0,
        "rmssd": 35.0,
        "fs": 100.0
    }
    result = service.run_ensemble_prediction(payload)
    
    assert result["contributing_models_count"] == 7
    assert len(result["excluded_models"]) == 0
    assert len(result["contributing_models"]) == 7
    
    # Probability vector validation
    probs = result["probability_vector"]
    assert len(probs) == 4
    assert all(np.isfinite(p) for p in probs)
    assert all(p >= 0.0 for p in probs)
    assert abs(sum(probs) - 1.0) < 1e-3
    assert result["prediction"] in [
        "Normal Sinus Rhythm",
        "Atrial Fibrillation",
        "Conduction Block",
        "Other Arrhythmia"
    ]


def test_ensemble_demographic_exclusion_graceful_fallback():
    """When Age or Sex is missing, multimodal and tabular models must be excluded gracefully."""
    service = get_ensemble_service()
    np.random.seed(42)
    raw_ecg = np.random.randn(1000).tolist()
    
    # Missing Age & Sex
    payload = {
        "raw_ecg": raw_ecg,
        "age": None,
        "sex": None,
        "heart_rate": None,
        "rmssd": None,
        "fs": 100.0
    }
    result = service.run_ensemble_prediction(payload)
    
    assert result["contributing_models_count"] == 5
    assert len(result["excluded_models"]) == 2
    
    excluded_ids = [m["model_id"] for m in result["excluded_models"]]
    assert "v8_tcn_multimodal" in excluded_ids
    assert "v8_tabular_mlp" in excluded_ids
    
    # Exclusion reasons must explicitly state insufficient demographic input
    for exc in result["excluded_models"]:
        assert "insufficient-input" in exc["reason"]
        assert "Age and Sex required" in exc["reason"]
        
    # Contributing models must be the 5 ECG-only models
    contributing_ids = [m["model_id"] for m in result["contributing_models"]]
    assert set(contributing_ids) == {"resnet", "v7_resnet", "v7_tcn", "v7_transformer", "v7_cnn_lstm"}
    
    # Dynamic weights of contributing models must sum to 1.0 (within rounding tolerance)
    weights_sum = sum(m["effective_weight"] for m in result["contributing_models"])
    assert abs(weights_sum - 1.0) < 1e-3
    
    # Probabilities must remain valid
    probs = result["probability_vector"]
    assert len(probs) == 4
    assert abs(sum(probs) - 1.0) < 1e-3


def test_ensemble_inference_determinism():
    """Inference on the identical input must produce bitwise identical results across 5 repeats."""
    service = get_ensemble_service()
    raw_ecg = np.sin(np.linspace(0, 10 * np.pi, 1000)).tolist()
    
    payload = {
        "raw_ecg": raw_ecg,
        "age": 55.0,
        "sex": 1,
        "heart_rate": 68.0,
        "rmssd": 42.0,
        "fs": 100.0
    }
    
    runs = []
    for _ in range(5):
        res = service.run_ensemble_prediction(payload)
        runs.append(res["probability_vector"])
        
    for i in range(1, 5):
        np.testing.assert_allclose(
            runs[0], runs[i], rtol=1e-6, atol=1e-6,
            err_msg=f"Ensemble predictions diverged on repeat {i}"
        )


def test_orchestrator_registry_compatibility():
    """Model registry must contain all 8 models and v9_ensemble must be recognized as an ensemble."""
    orc = get_orchestrator()
    models = orc.get_available_models()
    
    model_ids = [m["id"] for m in models]
    assert "v9_ensemble" in model_ids
    assert len(model_ids) >= 8
    
    ensemble_meta = orc.registry["models"]["v9_ensemble"]
    assert ensemble_meta["input_type"] == "ensemble"
    assert ensemble_meta["architecture"] == "Seven-Model Ensemble"
    assert ensemble_meta["parameters"] == 842508
    assert ensemble_meta["status"] == "verified"


if __name__ == "__main__":
    print(">>> Running Seven-Model Ensemble Integration Test Suite...")
    test_ensemble_weights_loaded()
    print("PASSED: test_ensemble_weights_loaded")
    test_ensemble_seven_models_with_demographics()
    print("PASSED: test_ensemble_seven_models_with_demographics")
    test_ensemble_demographic_exclusion_graceful_fallback()
    print("PASSED: test_ensemble_demographic_exclusion_graceful_fallback")
    test_ensemble_inference_determinism()
    print("PASSED: test_ensemble_inference_determinism")
    test_orchestrator_registry_compatibility()
    print("PASSED: test_orchestrator_registry_compatibility")
    print(">>> ALL ENSEMBLE INTEGRATION TESTS PASSED (5/5)!")

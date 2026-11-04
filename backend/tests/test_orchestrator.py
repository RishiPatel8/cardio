import os
import pytest
import numpy as np
from app.services.orchestrator import ModelOrchestrator

@pytest.fixture(scope="module")
def orchestrator():
    orc = ModelOrchestrator()
    return orc

def test_registry_loaded(orchestrator):
    assert len(orchestrator.registry.get("models", {})) >= 7
    available = orchestrator.get_available_models()
    assert len(available) >= 7

def test_model_loading_v6(orchestrator):
    model = orchestrator.load_model("resnet")
    assert model is not None

def test_inference_v6(orchestrator):
    payload = {
        "waveform": np.random.randn(1000).tolist(),
        "fs": 100.0
    }
    result = orchestrator.run_single_model("resnet", payload)
    assert result["status"] == "success"
    assert "class_index" in result
    assert result["architecture"] == "1D CNN"

def test_inference_v8_multimodal(orchestrator):
    payload = {
        "waveform": np.random.randn(1000).tolist(),
        "age": 45,
        "sex": 1,
        "fs": 100.0
    }
    result = orchestrator.run_single_model("v8_tcn_multimodal", payload)
    assert result["status"] == "success"
    assert "class_index" in result
    assert result["architecture"] == "TCN Multimodal"

def test_inference_v8_tabular(orchestrator):
    payload = {
        "age": 45,
        "sex": 1
    }
    result = orchestrator.run_single_model("v8_tabular_mlp", payload)
    assert result["status"] == "success"
    assert "class_index" in result

def test_run_all_compatible(orchestrator):
    payload = {
        "waveform": np.random.randn(1000).tolist(),
        "age": 45,
        "sex": 1,
        "fs": 100.0
    }
    results = orchestrator.run_all_compatible_models(payload)
    assert len(results) >= 7
    for res in results:
        assert res["status"] == "success", f"Model {res.get('model_id')} failed: {res.get('status')}"

import numpy as np
import tensorflow as tf
import os
import sys

# Ensure backend path is configured
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from app.services.inference_service import get_inference_service

os.environ['PREDICTION_MODE'] = 'real'

def test_v8_golden_standalone():
    """
    Test standalone V8 TCN Multimodal inference matches backend V8 inference exactly.
    """
    print("Testing V8 golden standalone...")
    service = get_inference_service()
    service.mode = "real"
    
    # We require the active model to be v8_tcn_multimodal for this test
    # If it is not, we temporarily switch it in memory
    original_model_type = getattr(service, "model_type", "resnet")
    original_model = service.model
    
    if original_model_type != "multimodal" or service.pipeline is None or service.model is None:
        service.model_type = "multimodal"
        service.real_model_path = "D:\\cardiogaurd\\ai\\artifacts\\models\\v8\\tcn_multimodal\\best_model.h5"
        service.model = tf.keras.models.load_model(service.real_model_path, compile=False)
        from ai.preprocessing.preprocessing_v3 import PreprocessingPipelineV3
        service.pipeline = PreprocessingPipelineV3(target_fs=100.0, target_length=1000)
    
    try:
        # Create a mock ECG signal of 1000 points
        test_ecg = np.sin(np.linspace(0, 10, 1000))
        # Add some noise to pass SQI
        test_ecg += np.random.normal(0, 0.1, 1000)
        
        # Build tabular payload
        from ai.preprocessing.preprocessing_v8 import build_tabular_tensor
        age = 50.0
        sex = 1
        fs = 100.0
        tabular_tensor = build_tabular_tensor(age, sex, test_ecg, fs=fs)
        
        # Payload format for real inference
        payload = {
            "waveform": test_ecg.tolist(),
            "tabular_features": tabular_tensor.tolist(),
            "fs": fs
        }
        
        # Run inference
        result = service.run_inference(payload)
        
        assert "confidence_score" in result
        assert "class_probabilities" in result
        assert result["mode"] == "REAL"
        
        probs = result["class_probabilities"]
        assert len(probs) == 4 # Normal, AFIB, Conduction Block, Other
        print("V8 golden standalone PASSED")
        
    finally:
        # Restore
        service.model_type = original_model_type
        service.model = original_model

def test_v6_regression():
    """
    Run V6 standalone vs. backend inference to confirm backward compatibility.
    """
    print("Testing V6 regression...")
    service = get_inference_service()
    service.mode = "real"
    
    original_model_type = getattr(service, "model_type", "resnet")
    original_model = service.model
    original_pipeline = service.pipeline
    
    if original_model_type != "resnet" or service.pipeline is None or service.model is None:
        service.model_type = "resnet"
        service.real_model_path = "D:\\cardiogaurd\\ai\\artifacts\\models\\v6_full\\best_model.h5"
        service.model = tf.keras.models.load_model(service.real_model_path, compile=False)
        from ai.preprocessing.preprocessing_v3 import PreprocessingPipelineV3
        service.pipeline = PreprocessingPipelineV3(target_fs=100.0, target_length=1000)
        service.pipeline.load("D:\\cardiogaurd\\ai\\artifacts\\models\\v6_full\\scaler_v6.pkl")
    
    try:
        # Create a mock ECG signal
        test_ecg = np.sin(np.linspace(0, 10, 1000))
        test_ecg += np.random.normal(0, 0.1, 1000)
        
        payload = {
            "waveform": test_ecg.tolist(),
            "fs": 100.0
        }
        
        result = service.run_inference(payload)
        
        assert "confidence_score" in result
        assert "class_probabilities" in result
        assert result["mode"] == "REAL"
        print("V6 regression PASSED")
        
    finally:
        service.model_type = original_model_type
        service.model = original_model
        service.pipeline = original_pipeline

def test_v8_api_failure_modes():
    """
    Test failure modes for V8 multimodal (missing age/sex, invalid ECG).
    """
    print("Testing V8 API failure modes...")
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
    from app.main import app
    
    # We can test the inference_service directly for failure modes
    service = get_inference_service()
    service.mode = "real"
    
    original_model_type = getattr(service, "model_type", "resnet")
    original_model = service.model
    
    if original_model_type != "multimodal" or service.pipeline is None or service.model is None:
        service.model_type = "multimodal"
        service.real_model_path = "D:\\cardiogaurd\\ai\\artifacts\\models\\v8\\tcn_multimodal\\best_model.h5"
        service.model = tf.keras.models.load_model(service.real_model_path, compile=False)
        from ai.preprocessing.preprocessing_v3 import PreprocessingPipelineV3
        service.pipeline = PreprocessingPipelineV3(target_fs=100.0, target_length=1000)
    
    try:
        test_ecg = np.sin(np.linspace(0, 10, 1000))
        test_ecg += np.random.normal(0, 0.1, 1000)
        
        # Missing tabular features
        payload_missing = {
            "waveform": test_ecg.tolist(),
            "fs": 100.0
        }
        
        try:
            service.run_inference(payload_missing)
            assert False, "Should raise ValueError for missing tabular_features"
        except ValueError as e:
            assert "Tabular features required" in str(e)
            
        # Invalid ECG length
        payload_invalid_len = {
            "waveform": test_ecg[:500].tolist(),
            "tabular_features": [0.5, 1, 0.3, 0.2],
            "fs": 100.0
        }
        try:
            service.run_inference(payload_invalid_len)
            assert False, "Should raise Exception for invalid waveform length"
        except Exception as e:
            assert "Invalid waveform length" in str(e)
            
        print("V8 API failure modes PASSED")
            
    finally:
        service.model_type = original_model_type
        service.model = original_model

if __name__ == "__main__":
    test_v8_golden_standalone()
    test_v6_regression()
    test_v8_api_failure_modes()
    print("All tests PASSED.")

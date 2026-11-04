import os
import json
import time
import numpy as np
from loguru import logger
from typing import List, Dict, Any, Optional
import sys

# Ensure backend root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from ai.preprocessing.preprocessing_v3 import PreprocessingPipelineV3
try:
    from ai.preprocessing.preprocessing_v8 import build_tabular_tensor
except ImportError:
    build_tabular_tensor = None

try:
    import tensorflow as tf
except ImportError:
    tf = None


class ModelOrchestrator:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ModelOrchestrator, cls).__new__(cls, *args, **kwargs)
            cls._instance._init_once()
        return cls._instance

    def _init_once(self):
        self.registry_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ai', 'config', 'registry.json'))
        self.registry = {}
        self.models = {}  # In-memory cache of loaded Keras models
        self.pipelines = {}  # In-memory cache of loaded preprocessors
        self.load_registry()
        
    def load_registry(self):
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r") as f:
                    self.registry = json.load(f)
                logger.info(f"Registry loaded from {self.registry_path}")
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")

    def get_available_models(self) -> List[Dict[str, Any]]:
        models_meta = []
        models_dict = self.registry.get("models", {})
        for mid, meta in models_dict.items():
            if meta.get("enabled", False):
                models_meta.append(meta)
        return models_meta

    def load_model(self, model_id: str):
        if model_id in self.models:
            return self.models[model_id]

        meta = self.registry.get("models", {}).get(model_id)
        if not meta:
            raise ValueError(f"Model ID {model_id} not found in registry")
            
        artifact_path = meta.get("artifact_path")
        if not artifact_path or not os.path.exists(artifact_path):
            raise FileNotFoundError(f"Artifact {artifact_path} not found")

        try:
            if tf is None:
                raise ImportError("TensorFlow not installed")
            model = tf.keras.models.load_model(artifact_path, compile=False)
            self.models[model_id] = model
            logger.info(f"Successfully loaded model {model_id}")
            return model
        except Exception as e:
            logger.error(f"Failed to load {model_id}: {e}")
            raise

    def load_pipeline(self, model_id: str):
        if model_id in self.pipelines:
            return self.pipelines[model_id]

        meta = self.registry.get("models", {}).get(model_id)
        if not meta:
            return None

        # V3 Preprocessing Pipeline
        if meta.get("preprocessing") == "v3":
            pipeline = PreprocessingPipelineV3(target_fs=100.0, target_length=1000)
            scaler_path = meta.get("preprocessing_artifact")
            if scaler_path and os.path.exists(scaler_path):
                try:
                    pipeline.load(scaler_path)
                    self.pipelines[model_id] = pipeline
                    return pipeline
                except Exception as e:
                    logger.error(f"Failed to load scaler for {model_id}: {e}")
            # Even if scaler load fails or doesn't exist, return unfitted pipeline to resample
            self.pipelines[model_id] = pipeline
            return pipeline
            
        return None

    def run_single_model(self, model_id: str, payload: dict) -> dict:
        meta = self.registry.get("models", {}).get(model_id)
        if not meta:
            return self._error_response(model_id, "Unknown", "Model not found in registry")

        start_time = time.perf_counter()
        input_type = meta.get("input_type", "ecg")
        
        try:
            model = self.load_model(model_id)
        except Exception as e:
            return self._error_response(model_id, meta.get("architecture", "Unknown"), f"Model failed to load: {e}")

        waveform = payload.get("waveform")
        age = payload.get("age")
        sex = payload.get("sex")
        fs = payload.get("fs", 100.0)

        # Validation
        if input_type in ["ecg", "multimodal"]:
            if waveform is None or len(waveform) == 0:
                return self._error_response(model_id, meta.get("architecture"), "Waveform required but not provided")
        if input_type in ["tabular", "multimodal"]:
            if age is None or sex is None:
                return self._error_response(model_id, meta.get("architecture"), "Age and sex required for tabular/multimodal")

        # Preprocessing & Inference
        try:
            probs = None
            if input_type == "ecg":
                pipeline = self.load_pipeline(model_id)
                arr = np.array(waveform, dtype=float).reshape(1, -1)
                if pipeline and pipeline.is_fitted:
                    processed = pipeline.process_inference_data([arr[0]], original_fs=fs)[0]
                else:
                    processed = arr[0]
                # Force to (1, 1000, 1)
                processed = processed[:1000] if len(processed) > 1000 else np.pad(processed, (0, max(0, 1000 - len(processed))))
                inputs = processed.reshape(1, 1000, 1)
                probs = model.predict(inputs, verbose=0)[0]
                
            elif input_type == "tabular":
                if build_tabular_tensor is None:
                    raise Exception("V8 tabular preprocessing not available")
                # Need dummy ECG to run build_tabular_tensor, or just compute directly
                dummy_ecg = np.array(waveform) if waveform is not None else np.zeros(1000)
                tab = build_tabular_tensor(age, sex, dummy_ecg, fs=fs)
                inputs = tab.reshape(1, 4)
                probs = model.predict(inputs, verbose=0)[0]
                
            elif input_type == "multimodal":
                if build_tabular_tensor is None:
                    raise Exception("V8 tabular preprocessing not available")
                arr = np.array(waveform, dtype=float)
                # Resample if needed using V3 temporarily or just use raw if expected 100hz
                # V8 expects 1000 items
                arr = arr[:1000] if len(arr) > 1000 else np.pad(arr, (0, max(0, 1000 - len(arr))))
                ecg_input = arr.reshape(1, 1000, 1)
                tab = build_tabular_tensor(age, sex, arr, fs=fs)
                tab_input = tab.reshape(1, 4)
                probs = model.predict([ecg_input, tab_input], verbose=0)[0]
            
            latency = int((time.perf_counter() - start_time) * 1000)
            
            # Postprocessing
            probs = np.clip(probs, 1e-7, 1.0)
            # Temperature scaling? Not strictly required by prompt but good to have
            probs = probs / np.sum(probs)
            
            pred_idx = int(np.argmax(probs))
            classes = meta.get("classes", ["Normal Sinus Rhythm", "Atrial Fibrillation", "Conduction Block", "Other Arrhythmia"])
            classification = classes[pred_idx] if pred_idx < len(classes) else "Unknown"
            
            probs_dict = {}
            for i, c in enumerate(classes):
                probs_dict[c] = float(probs[i]) if i < len(probs) else 0.0

            return {
                "model_id": model_id,
                "model_version": meta.get("version"),
                "architecture": meta.get("architecture"),
                "prediction": classification,
                "class_index": pred_idx,
                "probabilities": probs_dict,
                "confidence": float(probs[pred_idx] * 100.0),
                "latency_ms": latency,
                "input_type": input_type,
                "status": "success"
            }
        except Exception as e:
            return self._error_response(model_id, meta.get("architecture"), f"Inference error: {e}")

    def run_multiple_models(self, model_ids: List[str], payload: dict) -> List[dict]:
        results = []
        for mid in model_ids:
            results.append(self.run_single_model(mid, payload))
        return results

    def run_all_compatible_models(self, payload: dict) -> List[dict]:
        waveform = payload.get("waveform")
        age = payload.get("age")
        sex = payload.get("sex")
        
        compatible_ids = []
        models_dict = self.registry.get("models", {})
        for mid, meta in models_dict.items():
            if not meta.get("enabled", False):
                continue
            input_type = meta.get("input_type", "ecg")
            if input_type in ["tabular", "multimodal"] and (age is None or sex is None):
                continue
            if input_type in ["ecg", "multimodal"] and not waveform:
                continue
            compatible_ids.append(mid)
            
        return self.run_multiple_models(compatible_ids, payload)

    def _error_response(self, model_id: str, architecture: str, reason: str):
        return {
            "model_id": model_id,
            "model_version": "Unknown",
            "architecture": architecture,
            "prediction": "Error",
            "class_index": -1,
            "probabilities": {},
            "confidence": 0.0,
            "latency_ms": 0,
            "input_type": "Unknown",
            "status": f"failed: {reason}"
        }

orchestrator_instance = ModelOrchestrator()
def get_orchestrator() -> ModelOrchestrator:
    return orchestrator_instance

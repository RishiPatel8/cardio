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



def _resolve_path(p: str) -> str:
    if not p:
        return ""
    if os.path.exists(p):
        return p
    norm = p.replace("\\", "/")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    for marker in ["ai/", "backend/"]:
        if marker in norm:
            cand = os.path.join(project_root, norm[norm.find(marker):])
            if os.path.exists(cand):
                return cand
    cand = os.path.join(project_root, p.lstrip("/\\"))
    if os.path.exists(cand):
        return cand
    return p

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
            
        if meta.get("input_type") == "ensemble" or model_id == "v9_ensemble":
            self.models[model_id] = "v9_ensemble_aggregator"
            return "v9_ensemble_aggregator"

        artifact_path = _resolve_path(meta.get("artifact_path"))
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
            scaler_path = _resolve_path(meta.get("preprocessing_artifact"))
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

        if model_id == "v9_ensemble" or meta.get("input_type") == "ensemble":
            from app.services.ensemble_service import get_ensemble_service
            ensemble_service = get_ensemble_service()
            return ensemble_service.run_ensemble_prediction(payload)

        start_time = time.perf_counter()
        input_type = meta.get("input_type", "ecg")
        
        try:
            model = self.load_model(model_id)
        except Exception as e:
            return self._error_response(model_id, meta.get("architecture", "Unknown"), f"Model failed to load: {e}")

        waveform = payload.get("waveform") or payload.get("raw_ecg")
        age = payload.get("age")
        sex = payload.get("sex")
        fs = payload.get("fs", 100.0)

        # Validation
        if input_type in ["ecg", "multimodal"]:
            if waveform is None or len(waveform) == 0:
                return self._error_response(model_id, meta.get("architecture"), "Waveform required but not provided")

        if input_type in ["tabular", "multimodal"]:
            if age is None or sex is None:
                return self._error_response(model_id, meta.get("architecture"), "insufficient-input: Patient Age and Sex required")

        # Preprocessing & Inference
        try:
            raw_arr = np.array(waveform, dtype=float) if (waveform is not None and len(waveform) > 0) else np.zeros(1000, dtype=float)
            window_size = int(fs * 10)
            if window_size <= 0:
                window_size = 1000

            if len(raw_arr) >= window_size:
                raw_windows = [raw_arr[i:i + window_size] for i in range(0, len(raw_arr) - window_size + 1, window_size)]
            else:
                pad_len = max(0, window_size - len(raw_arr))
                raw_windows = [np.pad(raw_arr, (0, pad_len), 'constant')]

            # Apply SQI filtering to maintain strict parity with analyze_physionet
            from ai.preprocessing.signal_quality import assess_signal_quality
            valid_windows = []
            for w in raw_windows:
                is_valid, _ = assess_signal_quality(w)
                if is_valid:
                    valid_windows.append(w)
            windows = valid_windows if len(valid_windows) > 0 else raw_windows

            num_windows = len(windows)
            windows_arr = np.array(windows, dtype=np.float32)

            probs = None
            if input_type == "ecg":
                pipeline = self.load_pipeline(model_id)
                if pipeline and pipeline.is_fitted:
                    processed = pipeline.process_inference_data(windows_arr, original_fs=fs)
                else:
                    processed = windows_arr
                inputs = processed.reshape(num_windows, 1000, 1)
                batch_probs = model.predict(inputs, verbose=0)
                probs = np.mean(batch_probs, axis=0)
                
            elif input_type == "tabular":
                if build_tabular_tensor is None:
                    raise Exception("V8 tabular preprocessing not available")
                tab_list = [build_tabular_tensor(age, sex, w, fs=fs) for w in windows]
                inputs = np.array(tab_list, dtype=np.float32).reshape(num_windows, 4)
                batch_probs = model.predict(inputs, verbose=0)
                probs = np.mean(batch_probs, axis=0)
                
            elif input_type == "multimodal":
                if build_tabular_tensor is None:
                    raise Exception("V8 tabular preprocessing not available")
                pipeline = self.load_pipeline(model_id)
                if pipeline and pipeline.is_fitted:
                    processed = pipeline.process_inference_data(windows_arr, original_fs=fs)
                else:
                    processed = windows_arr
                inputs = processed.reshape(num_windows, 1000, 1)
                tab_list = [build_tabular_tensor(age, sex, w, fs=fs) for w in windows]
                tab_inputs = np.array(tab_list, dtype=np.float32).reshape(num_windows, 4)
                batch_probs = model.predict([inputs, tab_inputs], verbose=0)
                probs = np.mean(batch_probs, axis=0)
            
            latency = int((time.perf_counter() - start_time) * 1000)
            
            # Postprocessing & normalization
            probs = np.clip(probs, 1e-7, 1.0)
            probs = probs / np.sum(probs)
            
            pred_idx = int(np.argmax(probs))
            classes = meta.get("classes", ["Normal Sinus Rhythm", "Atrial Fibrillation", "Conduction Block", "Other Arrhythmia"])
            classification = classes[pred_idx] if pred_idx < len(classes) else "Unknown"
            confidence_pct = float(probs[pred_idx] * 100.0)
            prob_list = [float(p) for p in probs]

            probs_dict = {
                "Normal Sinus Rhythm": float(probs[0]),
                "Normal": float(probs[0] * 100.0),
                "Atrial Fibrillation": float(probs[1]),
                "AFIB": float(probs[1] * 100.0),
                "Conduction Block": float(probs[2] * 100.0),
                "Other Arrhythmia": float(probs[3] * 100.0) if len(probs) > 3 else 0.0,
            }

            return {
                "model_id": model_id,
                "model_version": meta.get("version"),
                "architecture": meta.get("architecture"),
                "prediction": classification,
                "classification": classification,
                "class_index": pred_idx,
                "probabilities": probs_dict,
                "class_probabilities": probs_dict,
                "probability_vector": prob_list,
                "confidence": confidence_pct,
                "confidence_score": confidence_pct,
                "latency_ms": latency,
                "inference_time_ms": latency,
                "input_type": input_type,
                "segments_analyzed": num_windows,
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
            if not meta.get("enabled", False) or mid == "v9_ensemble" or meta.get("input_type") == "ensemble":
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

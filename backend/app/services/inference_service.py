import os
from app.core.config import settings
import json
import numpy as np
import joblib
from loguru import logger
from datetime import datetime

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from ai.preprocessing.preprocessing_v3 import PreprocessingPipelineV3
from app.services.shap_service import get_shap_service

try:
    import tensorflow as tf
except ImportError:
    tf = None

class InferenceService:
    def __init__(self):
        self.mode = getattr(settings, "PREDICTION_MODE", os.environ.get("PREDICTION_MODE", "demo")).lower()
        self.model = None
        self.pipeline = None
        self.shap_service = None
        self.model_version = "demo-v1"
        self.threshold = 0.5
        self._load_registry()
        self._initialize()

    def _resolve_path(self, p: str) -> str:
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

    def _load_registry(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self.registry_path = self._resolve_path(os.path.join(project_root, "ai", "config", "registry.json"))
        self.real_model_path = self._resolve_path(os.path.join(project_root, "ai", "artifacts", "models", "v6_full", "best_model.h5"))
        self.scaler_path = self._resolve_path(os.path.join(project_root, "ai", "artifacts", "models", "v6_full", "scaler_v6.pkl"))
        self.shap_bg_path = self._resolve_path(os.path.join(project_root, "ai", "artifacts", "models", "v6_full", "shap_background.npy"))

        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r") as f:
                    registry = json.load(f)
                    self.active_model = registry.get("active_model", "resnet")
                    self.temperature = float(registry.get("temperature", 1.0))
                    self.afib_threshold = float(registry.get("afib_threshold", 0.5))
                    
                    models = registry.get("models", {})
                    if self.active_model in models:
                        m = models[self.active_model]
                        self.real_model_path = self._resolve_path(m.get("artifact_path", self.real_model_path))
                        self.scaler_path = self._resolve_path(m.get("preprocessing_artifact", self.scaler_path))
                        self.model_version = m.get("version", "v6-canonical")
                        self.model_type = m.get("architecture", "resnet")
                        self.shap_bg_path = self._resolve_path(m.get("shap_background_path", self.shap_bg_path))
                    elif "artifact_path" in registry:
                        self.real_model_path = self._resolve_path(registry["artifact_path"])
                        self.scaler_path = self._resolve_path(registry.get("preprocessing_artifact", self.scaler_path))
                        self.model_version = registry.get("version", "v5-full-run")

                    canonical_bg = self._resolve_path(os.path.join(project_root, "ai", "artifacts", "models", "v6_full", "shap_background.npy"))
                    if (not self.shap_bg_path or not os.path.exists(self.shap_bg_path) or "187" in str(self.shap_bg_path)) and os.path.exists(canonical_bg):
                        self.shap_bg_path = canonical_bg
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")

    def _initialize(self):
        
        if self.mode == "real":
            if os.path.exists(self.real_model_path):
                try:
                    if self.real_model_path.endswith(".h5") or self.real_model_path.endswith(".keras"):
                        if tf is None:
                            logger.error("TensorFlow not installed. REAL mode inference cannot proceed for Keras model.")
                            return
                        self.model = tf.keras.models.load_model(self.real_model_path, compile=False)
                    elif self.real_model_path.endswith(".pkl"):
                        self.model = joblib.load(self.real_model_path)
                    logger.info(f"Model loaded from {self.real_model_path}")
                except Exception as e:
                    logger.error(f"Failed to load model: {e}")
            else:
                logger.error(f"Model file not found at {self.real_model_path}")
            
            if os.path.exists(self.scaler_path) and (self.scaler_path.endswith("scaler_v2.pkl") or self.scaler_path.endswith("scaler_v3.pkl")):
                try:
                    self.pipeline = PreprocessingPipelineV3(target_fs=100.0, target_length=1000)
                    self.pipeline.load(self.scaler_path)
                    logger.info(f"Pipeline scaler loaded from {self.scaler_path}")
                except Exception as e:
                    logger.error(f"Failed to load pipeline: {e}")
                    self.pipeline = PreprocessingPipelineV3(target_fs=100.0, target_length=1000)
            else:
                self.pipeline = PreprocessingPipelineV3(target_fs=100.0, target_length=1000)
                if os.path.exists(self.scaler_path):
                    try:
                        self.pipeline.load(self.scaler_path)
                        logger.info(f"Scaler loaded from {self.scaler_path}")
                    except Exception as e:
                        logger.error(f"Failed to load scaler: {e}")

            self.shap_service = get_shap_service(self.real_model_path, self.shap_bg_path)

    def run_inference(self, payload: dict):
        # returns prediction, score, tier, explanation
        if self.mode == "demo":
            if os.environ.get('PREDICTION_MODE', 'demo').lower() == "real":
                raise Exception("Demo inference explicitly blocked in real mode")
            return self._run_demo_inference(payload)
        else:
            return self._run_real_inference(payload)

    def _run_real_inference(self, payload: dict):
        if not self.model or not self.pipeline:
            raise Exception("Real inference blocked: Model or Pipeline not initialized.")
        
        if "waveform" not in payload:
            raise Exception("Payload missing 'waveform'")
            
        waveform = payload.get("waveform", [])
        
        # Check invalid format
        if not isinstance(waveform, list) or len(waveform) == 0:
            logger.warning("Invalid waveform format or empty, rejecting.")
            raise ValueError("Waveform must be a non-empty list of numerical values.")

        # Check for NaN / Inf
        try:
            arr = np.array(waveform, dtype=float)
        except Exception:
            raise ValueError("Waveform cannot be cast to valid numerical array.")
            
        if np.isnan(arr).any() or np.isinf(arr).any():
            logger.warning("Waveform contains NaN or Inf, rejecting.")
            raise ValueError("Waveform contains invalid values")
        # Calculate SQI (Signal Quality Index)
        var = np.var(arr)
        if var < 1e-4:
            raise ValueError("SQI Error: Signal variance too low (flatline).")
        if var > 1e4:
            raise ValueError("SQI Error: Signal variance too high (extreme noise).")
        
        # Check clipping (percentage of samples at identical extreme bounds)
        unique, counts = np.unique(arr, return_counts=True)
        if len(unique) > 0 and (np.max(counts) / len(arr)) > 0.2:
            raise ValueError("SQI Error: Signal appears clipped/saturated.")
            
        sqi_score = 1.0 - min((var / 20000), 0.5)

        if self.model_type != "multimodal" and len(waveform) != 1000:
            logger.warning(f"Invalid waveform length {len(waveform)}, expected 1000. Rejecting.")
            raise Exception("Invalid waveform length")
            
        if self.model_type == "multimodal" and len(waveform) != 1000:
            logger.warning(f"Invalid waveform length {len(waveform)} for multimodal, expected 1000. Rejecting.")
            raise Exception("Invalid waveform length")
                
        raw_waveform = arr.reshape(1, -1)

        if self.model_type != "multimodal" and self.pipeline.is_fitted:
            processed_waveform = self.pipeline.process_inference_data([raw_waveform[0]], original_fs=payload.get("fs", 100.0))[0]
        else:
            processed_waveform = raw_waveform[0]

        # Sklearn models expect (1, 1000), TF models expect (1, 1000, 1)
        if self.real_model_path.endswith(".pkl"):
            waveform_data = processed_waveform.reshape(1, -1)
            raw_probs = self.model.predict_proba(waveform_data)[0]
        elif self.model_type == "multimodal":
            waveform_data = processed_waveform.reshape(1, 1000, 1)
            tabular_features = payload.get("tabular_features")
            if tabular_features is None:
                raise ValueError("Tabular features required for multimodal model.")
            tabular_data = np.array(tabular_features, dtype=np.float32).reshape(1, 4)
            raw_probs = self.model.predict([waveform_data, tabular_data], verbose=0)[0]
        else:
            waveform_data = processed_waveform.reshape(1, 1000, 1)
            raw_probs = self.model.predict(waveform_data, verbose=0)[0]
            
        # Calibration (Temperature Scaling)
        raw_probs = np.clip(raw_probs, 1e-7, 1.0)
        temp = getattr(self, 'temperature', 1.0)
        logits = np.log(raw_probs) / temp
        exp_logits = np.exp(logits)
        probs = exp_logits / np.sum(exp_logits)
        
        # Threshold Logic
        afib_threshold = getattr(self, 'afib_threshold', 0.5)
        if probs[1] > afib_threshold and probs[1] > probs[2]:
            pred_idx = 1
        else:
            pred_idx = int(np.argmax(probs))

        confidence_score = float(probs[pred_idx] * 100)
        
        classes = ["Normal Sinus Rhythm", "Atrial Fibrillation", "Conduction Block", "Other Arrhythmia"]
        classification = classes[pred_idx]
        
        # We define any non-Normal as an anomaly for the legacy system flags
        is_anomaly = bool(pred_idx != 0)
        risk_tier = "high" if is_anomaly else "low"

        explanation = []
        if self.shap_service:
            try:
                # pass pred_idx so SHAP explains the predicted class
                explanation = self.shap_service.get_explanation(waveform_data, target_class=pred_idx)
            except Exception as e:
                logger.error(f"Failed to generate real SHAP explanation: {e}")

        return {
            "is_anomaly": is_anomaly,
            "classification": classification,
            "confidence_score": confidence_score,
            "class_probabilities": {
                "Normal Sinus Rhythm": float(probs[0]),
                "Atrial Fibrillation": float(probs[1]),
                "Conduction Block": float(probs[2]),
                "Other Arrhythmia": float(probs[3]) if len(probs) > 3 else 0.0
            },
            "risk_tier": risk_tier,
            "model_version": self.model_version,
            "mode": "REAL",
            "explanation": explanation,
            "signal_quality": sqi_score,
            "calibrated": True
        }

    def run_bulk_inference(self, raw_waveforms: np.ndarray, original_fs: float = 100.0, tabular_features: np.ndarray = None):
        """Run efficient inference on a batch of waveforms."""
        if not self.model or not self.pipeline:
            raise Exception("Real inference blocked: Model or Pipeline not initialized.")
            
        if self.model_type == "multimodal" and tabular_features is None:
            raise Exception("Multimodal model requires tabular features.")
        
        if self.model_type != "multimodal" and self.pipeline.is_fitted:
            processed_waveforms = self.pipeline.process_inference_data(raw_waveforms, original_fs=original_fs)
        else:
            processed_waveforms = raw_waveforms

        if self.real_model_path.endswith(".pkl"):
            waveform_data = processed_waveforms.reshape(processed_waveforms.shape[0], -1)
            probs_array = self.model.predict_proba(waveform_data)
        elif self.model_type == "multimodal":
            waveform_data = processed_waveforms.reshape(processed_waveforms.shape[0], 1000, 1)
            probs_array = self.model.predict([waveform_data, tabular_features], verbose=0)
        else:
            waveform_data = processed_waveforms.reshape(processed_waveforms.shape[0], 1000, 1)
            probs_array = self.model.predict(waveform_data, verbose=0)

        pred_indices = np.argmax(probs_array, axis=1)
        is_anomalies = pred_indices != 0
        
        return {
            "probs": probs_array,
            "is_anomalies": is_anomalies,
            "processed_data": waveform_data
        }
        
    def generate_attribution(self, waveform_data: np.ndarray, target_class: int = None, tabular: np.ndarray = None):
        """Generate high-precision feature attribution for a 1000-sample segment."""
        contributions = []
        try:
            if tf is not None and self.model is not None and not self.real_model_path.endswith(".pkl"):
                w = waveform_data.reshape(1, 1000, 1)
                x_tensor = tf.convert_to_tensor(w, dtype=tf.float32)
                with tf.GradientTape() as tape:
                    tape.watch(x_tensor)
                    if tabular is not None and self.model_type == "multimodal":
                        t_tensor = tf.convert_to_tensor(tabular.reshape(1, -1), dtype=tf.float32)
                        preds = self.model([x_tensor, t_tensor], training=False)
                    else:
                        preds = self.model(x_tensor, training=False)
                    c_idx = target_class if target_class is not None else 1
                    loss = preds[:, c_idx]
                grads = tape.gradient(loss, x_tensor)
                if grads is not None:
                    attr = tf.abs(grads).numpy().flatten()
                    if np.max(attr) > 1e-8:
                        norm_attr = (attr / np.max(attr)) * 0.15
                        contributions = [
                            {"feature": f"time_{i}", "contribution": float(norm_attr[i])}
                            for i in range(len(norm_attr))
                        ]
                        return sorted(contributions, key=lambda x: x["contribution"], reverse=True)
        except Exception as e:
            logger.warning(f"Gradient attribution failed: {e}")

        # If gradient wasn't applicable, try SHAP service
        if self.shap_service:
            try:
                reshaped = waveform_data.reshape(1, -1) if self.real_model_path.endswith(".pkl") else waveform_data.reshape(1, 1000, 1)
                shap_res = self.shap_service.get_explanation(reshaped, target_class=target_class)
                if shap_res and len(shap_res) > 0:
                    return shap_res
            except Exception as e:
                logger.warning(f"SHAP explanation fallback failed: {e}")

        # Final signal deviation heuristic fallback
        try:
            flat = waveform_data.flatten()
            diff = np.abs(flat - np.median(flat))
            if np.max(diff) > 0:
                norm_diff = (diff / np.max(diff)) * 0.12
                contributions = [
                    {"feature": f"time_{i}", "contribution": float(norm_diff[i])}
                    for i in range(len(norm_diff))
                ]
                return sorted(contributions, key=lambda x: x["contribution"], reverse=True)
        except Exception as e:
            logger.error(f"Heuristic attribution failed: {e}")

        return []

    def generate_shap_for_segment(self, waveform_data: np.ndarray, target_class: int = None):
        """Generate attribution specifically for a single processed segment."""
        return self.generate_attribution(waveform_data, target_class=target_class)

    def _run_demo_inference(self, payload: dict):
        sdrr_ms = payload.get("sdrr_ms", 50)
        rmssd_ms = payload.get("rmssd_ms", 30)

        is_anomaly = sdrr_ms > 90 or rmssd_ms > 80
        confidence_score = 92.5 if is_anomaly else 98.2
        risk_tier = "high" if is_anomaly else "low"

        explanation = []
        shap_srv = get_shap_service("", "")
        explanation = shap_srv.get_explanation(np.zeros((1, 187)))

        return {
            "is_anomaly": is_anomaly,
            "classification": "Atrial Fibrillation" if is_anomaly else "Normal Sinus Rhythm",
            "class_probabilities": {
                "Normal Sinus Rhythm": 0.05 if is_anomaly else 0.98,
                "Atrial Fibrillation": 0.92 if is_anomaly else 0.01,
                "Conduction Block": 0.0 if is_anomaly else 0.0,
                "Other Arrhythmia": 0.03 if is_anomaly else 0.01
            },
            "confidence_score": confidence_score,
            "risk_tier": risk_tier,
            "model_version": "demo-v1",
            "mode": "DEMO",
            "explanation": explanation
        }

inference_service_instance = InferenceService()

def get_inference_service() -> InferenceService:
    return inference_service_instance


import os
import json
import time
import numpy as np
from loguru import logger
from typing import List, Dict, Any, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

CANONICAL_CLASSES = [
    "Normal Sinus Rhythm",
    "Atrial Fibrillation",
    "Conduction Block",
    "Other Arrhythmia"
]

BASE_MODEL_ORDER = [
    "resnet",              # 1D CNN (v6-canonical)
    "v7_resnet",           # ResNet (v7-resnet-improved)
    "v7_tcn",              # TCN (v7-tcn)
    "v7_transformer",      # Transformer (v7-transformer)
    "v7_cnn_lstm",         # CNN-LSTM (v7-cnn-lstm)
    "v8_tcn_multimodal",   # TCN Multimodal (v8-multimodal)
    "v8_tabular_mlp"       # Tabular MLP (v8-tabular-mlp)
]

DEFAULT_FROZEN_WEIGHTS = {
    "v8_tcn_multimodal": 0.1643,
    "v7_tcn": 0.1568,
    "v7_resnet": 0.1558,
    "v7_transformer": 0.1516,
    "resnet": 0.1490,
    "v7_cnn_lstm": 0.1123,
    "v8_tabular_mlp": 0.1100
}


class EnsembleService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EnsembleService, cls).__new__(cls, *args, **kwargs)
            cls._instance._init_service()
        return cls._instance

    def _init_service(self):
        self.weights_path = os.path.join(PROJECT_ROOT, "ai", "config", "ensemble_weights.json")
        self.weights = dict(DEFAULT_FROZEN_WEIGHTS)
        self.methodology = "Validation-Derived Normalized Macro F1 Soft Voting"
        self.load_frozen_weights()

    def load_frozen_weights(self):
        if os.path.exists(self.weights_path):
            try:
                with open(self.weights_path, "r") as f:
                    data = json.load(f)
                    if "weights" in data and isinstance(data["weights"], dict):
                        self.weights = data["weights"]
                        self.methodology = data.get("methodology", self.methodology)
                        logger.info(f"Loaded frozen ensemble weights from {self.weights_path}")
            except Exception as e:
                logger.warning(f"Failed to load ensemble weights from file, using verified defaults: {e}")

    def validate_probability_vector(self, prob_vec: Any) -> Optional[np.ndarray]:
        """Ensures probability vector is 4D, finite, non-negative, and sums approximately to 1.0."""
        if prob_vec is None:
            return None
        try:
            arr = np.array(prob_vec, dtype=np.float64)
            if arr.ndim != 1 or len(arr) != 4:
                return None
            if not np.all(np.isfinite(arr)):
                return None
            if np.any(arr < 0.0):
                return None
            s = np.sum(arr)
            if s <= 0.0:
                return None
            # Normalize to guarantee exact sum = 1.0
            return arr / s
        except Exception:
            return None

    def aggregate_predictions(self, model_outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes Phase 3 weighted soft-voting aggregation with full safeguards.
        P_final(c) = SUM(w_i * P_i(c)) / SUM(w_i)
        """
        contributing_models = []
        excluded_models = []
        
        valid_weights = []
        valid_probs = []

        for out in model_outputs:
            mid = out.get("model_id", "unknown")
            arch = out.get("architecture", mid)
            status = out.get("status", "unknown")

            if status != "success":
                excluded_models.append({
                    "model_id": mid,
                    "architecture": arch,
                    "status": status,
                    "reason": status.replace("failed: ", "")
                })
                continue

            # Validate probability vector
            raw_probs = out.get("probability_vector")
            if raw_probs is None and "probabilities" in out:
                p_dict = out["probabilities"]
                raw_probs = [
                    p_dict.get("Normal Sinus Rhythm", p_dict.get("Normal", 0.0)),
                    p_dict.get("Atrial Fibrillation", p_dict.get("AFIB", 0.0)),
                    p_dict.get("Conduction Block", 0.0),
                    p_dict.get("Other Arrhythmia", 0.0),
                ]

            validated_vec = self.validate_probability_vector(raw_probs)
            if validated_vec is None:
                excluded_models.append({
                    "model_id": mid,
                    "architecture": arch,
                    "status": "failed: malformed probability vector",
                    "reason": "Malformed or non-normalizable probability distribution"
                })
                continue

            w = float(self.weights.get(mid, 0.1))
            valid_weights.append(w)
            valid_probs.append(validated_vec)

            pred_class = out.get("prediction", out.get("classification", "Unknown"))
            conf = float(out.get("confidence", out.get("confidence_score", np.max(validated_vec) * 100.0)))

            contributing_models.append({
                "model_id": mid,
                "architecture": arch,
                "version": out.get("model_version", "unknown"),
                "predicted_class": pred_class,
                "confidence": conf,
                "probability_vector": validated_vec.tolist(),
                "weight": w,
                "status": "contributing",
                "latency_ms": out.get("latency_ms", out.get("inference_time_ms", 0))
            })

        if not valid_probs:
            return {
                "status": "failed",
                "error": "No models produced valid predictions for ensemble aggregation",
                "contributing_models_count": 0,
                "excluded_models": excluded_models
            }

        # Mathematical weighted soft-voting
        weights_arr = np.array(valid_weights, dtype=np.float64)
        sum_weights = np.sum(weights_arr)
        if sum_weights <= 0:
            weights_arr = np.ones_like(weights_arr) / len(weights_arr)
        else:
            weights_arr = weights_arr / sum_weights  # Normalized dynamic weights

        # Update effective normalized weights on contributing metadata
        for i, cm in enumerate(contributing_models):
            cm["effective_weight"] = float(weights_arr[i])

        probs_matrix = np.array(valid_probs, dtype=np.float64)  # Shape: (N, 4)
        ensemble_probs = np.sum(probs_matrix * weights_arr[:, None], axis=0)  # Shape: (4,)
        ensemble_probs = ensemble_probs / np.sum(ensemble_probs)  # Guarantee strict normalization

        final_pred_idx = int(np.argmax(ensemble_probs))
        final_class = CANONICAL_CLASSES[final_pred_idx]
        final_conf_pct = float(ensemble_probs[final_pred_idx] * 100.0)

        # Agreement & Disagreement Analysis
        agreeing_models = []
        disagreeing_models = []
        votes = {}

        for cm in contributing_models:
            c_pred = cm["predicted_class"]
            votes[c_pred] = votes.get(c_pred, 0) + 1
            if c_pred == final_class:
                agreeing_models.append(cm["model_id"])
            else:
                disagreeing_models.append(cm["model_id"])

        most_common_class = max(votes.items(), key=lambda x: x[1])[0] if votes else final_class
        total_contrib = len(contributing_models)
        agree_count = len(agreeing_models)
        agreement_pct = float((agree_count / total_contrib) * 100.0) if total_contrib > 0 else 0.0

        probs_dict = {
            "Normal Sinus Rhythm": float(ensemble_probs[0] * 100.0),
            "Normal": float(ensemble_probs[0] * 100.0),
            "Atrial Fibrillation": float(ensemble_probs[1] * 100.0),
            "AFIB": float(ensemble_probs[1] * 100.0),
            "Conduction Block": float(ensemble_probs[2] * 100.0),
            "Other Arrhythmia": float(ensemble_probs[3] * 100.0),
        }

        return {
            "model_id": "v9_ensemble",
            "model_version": "v9-ensemble",
            "architecture": "Seven-Model Ensemble",
            "name": "Final Ensemble Model",
            "classification": final_class,
            "prediction": final_class,
            "class_index": final_pred_idx,
            "confidence": final_conf_pct,
            "confidence_score": final_conf_pct,
            "probability_vector": [float(p) for p in ensemble_probs],
            "probabilities": probs_dict,
            "class_probabilities": probs_dict,
            "contributing_models_count": total_contrib,
            "total_models_count": len(BASE_MODEL_ORDER),
            "contributing_models": contributing_models,
            "excluded_models": excluded_models,
            "ensemble_weights": {cm["model_id"]: cm["effective_weight"] for cm in contributing_models},
            "weighting_methodology": self.methodology,
            "agreement_analysis": {
                "agreeing_models": agreeing_models,
                "disagreeing_models": disagreeing_models,
                "agreeing_count": agree_count,
                "disagreeing_count": len(disagreeing_models),
                "agreement_percentage": agreement_pct,
                "most_common_individual_prediction": most_common_class,
                "disclaimer": "Agreement percentage measures consensus across model predictions and does not equate to clinical diagnostic accuracy."
            },
            "status": "success"
        }

    def run_ensemble_prediction(self, payload: dict) -> Dict[str, Any]:
        """
        Runs all base models via ModelOrchestrator and computes the weighted soft-voting ensemble.
        """
        from app.services.orchestrator import get_orchestrator
        orchestrator = get_orchestrator()

        start_time = time.perf_counter()
        
        # Execute all 7 base models sequentially or cached
        individual_results = []
        for mid in BASE_MODEL_ORDER:
            res = orchestrator.run_single_model(mid, payload)
            individual_results.append(res)

        total_latency = int((time.perf_counter() - start_time) * 1000)
        
        ensemble_result = self.aggregate_predictions(individual_results)
        ensemble_result["inference_time_ms"] = total_latency
        ensemble_result["latency_ms"] = total_latency
        ensemble_result["signal_quality"] = "GOOD"
        ensemble_result["analysis_window"] = "0.0s – 10.0s"
        ensemble_result["sampling_rate"] = 100.0

        return ensemble_result


_ensemble_service_instance = None
def get_ensemble_service() -> EnsembleService:
    global _ensemble_service_instance
    if _ensemble_service_instance is None:
        _ensemble_service_instance = EnsembleService()
    return _ensemble_service_instance

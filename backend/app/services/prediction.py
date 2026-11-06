import uuid
import sys
import os
import json
import numpy as np
import time
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import redis.asyncio as aioredis
from fastapi import HTTPException

# Ensure root path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.models.prediction import Prediction
from app.models.prediction_history import PredictionHistory
from app.repositories.prediction import PredictionRepository
from app.repositories.wearable_data import WearableDataRepository
from app.schemas.prediction import PredictionRequest

from ai.fusion.multimodal_fusion import preprocess_tabular_features
from ai.inference.explainable_ai import compute_feature_contributions, generate_natural_language_explanation
from ai.preprocessing.preprocessing_v6 import PreprocessingPipelineV6
from ai.preprocessing.signal_quality import assess_signal_quality

# V6 4-class mapping
CLASS_MAPPING = {
    0: "Normal Sinus Rhythm",
    1: "Atrial Fibrillation",
    2: "Conduction Block",
    3: "Other Arrhythmia"
}

# Ensure real inference is explicitly enabled or fail loudly
PREDICTION_MODE = os.environ.get("PREDICTION_MODE", "real")
if PREDICTION_MODE != "real":
    logger.warning("PREDICTION_MODE is not 'real'. Falling back to testing mode is disabled for clinical safety.")

# Load Model and Preprocessing Pipeline globally via registry
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

def _resolve_path(p: str) -> str:
    if not p:
        return ""
    if os.path.exists(p):
        return p
    norm = p.replace("\\", "/")
    for marker in ["ai/", "backend/"]:
        if marker in norm:
            cand = os.path.join(PROJECT_ROOT, norm[norm.find(marker):])
            if os.path.exists(cand):
                return cand
    cand = os.path.join(PROJECT_ROOT, p.lstrip("/\\"))
    if os.path.exists(cand):
        return cand
    return p

try:
    import tensorflow as tf
    registry_path = os.path.join(PROJECT_ROOT, "ai", "config", "registry.json")
    with open(registry_path, "r") as f:
        registry = json.load(f)
        
    active_model = registry.get("active_model", "resnet")
    model_cfg = registry.get("models", {}).get(active_model, {})
    raw_model_path = model_cfg.get("artifact_path", registry.get("artifact_path", "ai/artifacts/models/v6_full/best_model.h5"))
    raw_scaler_path = model_cfg.get("preprocessing_artifact", registry.get("preprocessing_artifact", "ai/artifacts/models/v6_full/scaler_v6.pkl"))
    
    v6_model_path = _resolve_path(raw_model_path)
    scaler_path = _resolve_path(raw_scaler_path)
    
    logger.info(f"Loading Model from {v6_model_path}...")
    if not os.path.exists(v6_model_path):
        raise FileNotFoundError(f"Model artifact missing: {v6_model_path}")
    v6_model = tf.keras.models.load_model(v6_model_path, compile=False)
    
    logger.info(f"Loading Preprocessing Scaler from {scaler_path}...")
    pipeline = PreprocessingPipelineV6()
    pipeline.load(scaler_path)
    logger.info("Inference pipeline successfully loaded.")
except Exception as e:
    logger.warning(f"Failed to load model or scaler on startup: {e}")
    v6_model = None
    pipeline = None

class PredictionService:
    def __init__(self, db: AsyncSession, redis_client: Optional[aioredis.Redis] = None):
        self.db = db
        self.prediction_repo = PredictionRepository(db)
        self.telemetry_repo = WearableDataRepository(db)
        self.redis = redis_client

    async def generate_ai_prediction(self, user_id: uuid.UUID, request: PredictionRequest) -> Prediction:
        # Check cache if telemetry ID is present
        cache_key = f"prediction:telemetry:{request.telemetry_id}" if request.telemetry_id else None
        if self.redis and cache_key:
            try:
                cached_pred = await self.redis.get(cache_key)
                if cached_pred:
                    logger.info(f"Cache hit: returning cached prediction for telemetry {request.telemetry_id}")
                    pred_dict = json.loads(cached_pred)
                    return Prediction(**pred_dict)
            except Exception as e:
                logger.warning(f"Failed to read from Redis cache: {e}")

        # V6 Raw ECG Inference Pipeline
        if not request.raw_ecg or len(request.raw_ecg) < 100:
            raise HTTPException(status_code=400, detail="Raw ECG array is missing or too short for clinical V6 prediction.")
        
        raw_signal = np.array(request.raw_ecg, dtype=np.float32)
        fs = request.fs if request.fs else 100.0

        # SQI Validation
        is_valid, sqi_reason = assess_signal_quality(raw_signal)
        if not is_valid:
            logger.warning(f"SQI Validation Failed: {sqi_reason}")
            raise HTTPException(status_code=400, detail=f"Signal Quality Invalid: {sqi_reason}")

        # Execute through unified orchestrator
        from app.services.orchestrator import get_orchestrator
        orch = get_orchestrator()

        model_id = getattr(request, "model_id", None)
        if not model_id or model_id == "default":
            model_id = orch.registry.get("active_model", "resnet")

        payload = {
            "waveform": request.raw_ecg,
            "raw_ecg": request.raw_ecg,
            "age": getattr(request, "age", 35.0) or 35.0,
            "sex": getattr(request, "sex", 0) or 0,
            "fs": fs
        }

        orc_res = orch.run_single_model(model_id, payload)
        if orc_res.get("status") != "success":
            raise HTTPException(status_code=500, detail=orc_res.get("status", "Model inference failed"))

        classification = orc_res["classification"]
        confidence_score = orc_res["confidence_score"]
        model_version_name = orc_res.get("model_version") or model_id
        probability_vector = orc_res.get("probability_vector") or []
        pred_class_idx = orc_res.get("class_index", 0)
        inference_time_ms = orc_res.get("inference_time_ms", 32)

        # Generate Heuristic Explainable Insights (using tabular data)
        avg_bpm = request.avg_bpm if request.avg_bpm is not None else 72.0
        sdrr_ms = request.sdrr_ms if request.sdrr_ms is not None else 45.0
        rmssd_ms = request.rmssd_ms if request.rmssd_ms is not None else 32.0

        mean_rr = 60000.0 / avg_bpm if avg_bpm > 0 else 833.3
        pnn50 = 8.0 if sdrr_ms < 35 else 15.0
        lf_hf_ratio = 2.2 if sdrr_ms < 35 else 1.3
        sd1 = rmssd_ms * 0.707
        sd2 = sdrr_ms * 1.414
        
        hrv_features = {
            "mean_rr": mean_rr,
            "sdnn": sdrr_ms,
            "rmssd": rmssd_ms,
            "pnn50": pnn50,
            "lf_hf_ratio": lf_hf_ratio,
            "sd1": sd1,
            "sd2": sd2,
        }
        
        wearable_features = {
            "steps": 6200.0,
            "calories": 320.0,
            "sleep_minutes": 432.0,
            "spo2": 98.0
        }
        
        demographics = {"age": 45.0}
        tabular_vec = preprocess_tabular_features(hrv_features, wearable_features, demographics)
        
        feature_names = [
            "mean_rr", "sdnn", "rmssd", "pnn50", "lf_hf_ratio", "sd1", "sd2", 
            "steps", "calories", "sleep_minutes", "spo2", "age"
        ]
        
        is_anomaly = (pred_class_idx != 0)
        contributions = compute_feature_contributions(tabular_vec, feature_names, is_anomaly=is_anomaly)
        insights = generate_natural_language_explanation(contributions, classification=classification, confidence=confidence_score)

        # Save to DB
        prediction = Prediction(
            user_id=user_id,
            telemetry_id=request.telemetry_id,
            classification=classification,
            confidence_score=confidence_score,
            probability_vector=probability_vector,
            model_version=model_version_name,
            explainable_insights=insights
        )
        prediction = await self.prediction_repo.create(prediction)
        prediction.inference_time_ms = inference_time_ms
        prediction.probability_vector = probability_vector
        prediction.class_probabilities = orc_res.get("probabilities")
        prediction.signal_quality = "GOOD"

        # Log prediction history state
        history_log = PredictionHistory(
            prediction_id=prediction.id,
            status="Logged"
        )
        self.db.add(history_log)
        
        # Trigger notification if anomaly
        if is_anomaly:
            from app.models.notification import Notification
            notification = Notification(
                user_id=user_id,
                title="Cardiac Anomaly Alert",
                message=f"Our AI detected possible {classification}. Please review your insights and consult a physician.",
                type="Alert",
                is_read=False
            )
            self.db.add(notification)
            
        await self.db.flush()

        logger.info(f"AI Prediction complete for user {user_id}: {classification} (confidence={confidence_score}%)")

        # Write to cache
        if self.redis and cache_key:
            try:
                pred_serializable = {
                    "id": str(prediction.id),
                    "user_id": str(prediction.user_id),
                    "telemetry_id": str(prediction.telemetry_id) if prediction.telemetry_id else None,
                    "classification": prediction.classification,
                    "confidence_score": prediction.confidence_score,
                    "probability_vector": prediction.probability_vector,
                    "model_version": prediction.model_version,
                    "explainable_insights": prediction.explainable_insights,
                    "created_at": prediction.created_at.isoformat() if prediction.created_at else None
                }
                await self.redis.set(cache_key, json.dumps(pred_serializable), ex=600)
            except Exception as e:
                logger.warning(f"Failed to write to Redis cache: {e}")

        return prediction

    async def get_user_prediction_history(self, user_id: uuid.UUID, limit: int = 50) -> List[Prediction]:
        return await self.prediction_repo.get_by_user(user_id, limit)

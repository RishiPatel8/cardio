from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

from app.database.firestore import get_db
from app.services.inference_service import get_inference_service, InferenceService
from app.services.auth_service import get_current_user
from loguru import logger

router = APIRouter()

class PredictionRequest(BaseModel):
    user_id: str = Field(default="", description="Authenticated user ID (overridden by token)")
    avg_bpm: float = Field(default=60.0, description="Calculated heart rate")
    sdrr_ms: float = Field(default=50.0, description="SDRR in ms")
    rmssd_ms: float = Field(default=30.0, description="RMSSD in ms")
    waveform: List[float] = Field(default=[], description="187-length ECG waveform")
    source: str = Field(default="simulator", description="Source of data (simulator/health_connect)")

class AIResultResponse(BaseModel):
    classification: str
    confidence_score: float
    class_probabilities: dict = {}
    model_version: str
    explainable_insights: List[str]
    mode: str
    prediction_id: str = ""

@router.post("/", response_model=AIResultResponse)
@router.post("/predict", response_model=AIResultResponse)
async def run_prediction(
    input_data: PredictionRequest,
    inference_service: InferenceService = Depends(get_inference_service),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Enforce True User Identity
        uid = current_user.get("uid")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
            
        input_data.user_id = uid

        # 1. Run inference
        result = inference_service.run_inference(input_data.dict())
        
        is_anomaly = result["is_anomaly"]
        classification = result["classification"]
        confidence_score = result["confidence_score"]
        class_probabilities = result.get("class_probabilities", {})
        model_ver = result["model_version"]
        mode_str = result["mode"]
        explanation = result["explanation"]
        risk_tier = result["risk_tier"]
        
        # 2. Format insights
        insights = [f"Mode: {mode_str}"]
        if mode_str == "REAL":
            insights.append(f"AI Classification: {classification} ({confidence_score:.1f}% confidence)")
            if explanation and len(explanation) > 0:
                top_feature = explanation[0]
                insights.append(f"Top variance driver: {top_feature.get('feature', 'Unknown')} ({top_feature.get('contribution', 0):.4f})")
        else:
            insights.append(f"Average heart rate registered at {input_data.avg_bpm} bpm.")
            if is_anomaly:
                insights.append(f"Abnormal SDRR score of {input_data.sdrr_ms}ms indicating high HRV.")
            else:
                insights.append(f"Stable SDRR metric of {input_data.sdrr_ms}ms matching sinus rhythm patterns.")
        
        pred_id = ""
        # 3. Persist to Firestore
        db = get_db()
        if db:
            try:
                pred_doc = db.collection("users").document(uid).collection("predictions").document()
                pred_data = {
                    "user_id": uid,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "risk_score": confidence_score,
                    "risk_tier": risk_tier,
                    "model_version": model_ver,
                    "pathway": "waveform" if mode_str == "REAL" else "trend",
                    "confidence": confidence_score,
                    "class_probabilities": class_probabilities,
                    "source": input_data.source,
                    "isMedicalDiagnosis": False,
                    "mode": mode_str,
                    "explanation_ref": pred_doc.id,
                    "classification": classification
                }
                pred_doc.set(pred_data)
                pred_id = pred_doc.id
                
                exp_doc = db.collection("users").document(uid).collection("explanations").document(pred_doc.id)
                exp_data = {
                    "prediction_id": pred_doc.id,
                    "user_id": uid,
                    "feature_contributions": explanation,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                exp_doc.set(exp_data)
                
            except Exception as e:
                logger.error(f"Failed to log prediction to Firestore: {e}")

        return AIResultResponse(
            classification=classification,
            confidence_score=confidence_score,
            class_probabilities=class_probabilities,
            model_version=model_ver,
            explainable_insights=insights,
            mode=mode_str,
            prediction_id=pred_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_prediction_history(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    try:
        uid = current_user.get("uid")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid authentication token")

        db = get_db()
        if not db:
            return []

        preds_ref = db.collection("users").document(uid).collection("predictions")
        query = preds_ref.order_by("timestamp", direction="DESCENDING").limit(limit)
        docs = query.stream()

        history = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            history.append(data)

        return history
    except Exception as e:
        logger.error(f"Failed to fetch prediction history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


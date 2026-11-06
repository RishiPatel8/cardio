from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict
import redis.asyncio as aioredis
from app.core.dependencies import get_current_user, get_db, get_redis
from app.models.user import User
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.prediction import PredictionService
from app.services.orchestrator import get_orchestrator

router = APIRouter()

class CompareRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    model_ids: Optional[str] = None
    raw_ecg: Optional[List[float]] = None
    waveform: Optional[List[float]] = None
    avg_bpm: Optional[float] = None
    sdrr_ms: Optional[float] = None
    rmssd_ms: Optional[float] = None
    age: Optional[float] = 35.0
    sex: Optional[int] = 0
    fs: Optional[float] = 100.0

@router.post("", response_model=PredictionResponse, summary="Run AI Prediction")
async def run_ai_prediction(
    request_data: PredictionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis)
):
    """Execute deep learning CNN-LSTM classification on synchronized vital streams."""
    service = PredictionService(db, redis_client)
    return await service.generate_ai_prediction(current_user.id, request_data)

@router.post("/compare", summary="Compare Multiple Models via JSON")
async def compare_models_json(
    req: CompareRequest,
    current_user: User = Depends(get_current_user)
):
    orchestrator = get_orchestrator()
    sig = req.waveform or req.raw_ecg or []
    payload = {
        "waveform": sig,
        "age": req.age if req.age is not None else 35.0,
        "sex": req.sex if req.sex is not None else 0,
        "fs": req.fs if req.fs is not None else 100.0
    }
    if req.model_ids:
        ids_list = [m.strip() for m in req.model_ids.split(",")]
        results = orchestrator.run_multiple_models(ids_list, payload)
    else:
        results = orchestrator.run_all_compatible_models(payload)
    return {"comparisons": results}

@router.post("/ensemble", summary="Run Seven-Model Ensemble via JSON")
async def run_ensemble_json(
    req: CompareRequest,
    current_user: User = Depends(get_current_user)
):
    """Execute the Seven-Model Weighted Soft-Voting Ensemble on telemetry JSON."""
    from app.services.ensemble_service import get_ensemble_service
    ensemble_service = get_ensemble_service()
    sig = req.waveform or req.raw_ecg or []
    payload = {
        "waveform": sig,
        "age": req.age,
        "sex": req.sex,
        "fs": req.fs if req.fs is not None else 100.0
    }
    return ensemble_service.run_ensemble_prediction(payload)

@router.get("/history", response_model=List[PredictionResponse], summary="Get Prediction History")
async def get_prediction_history(
    limit: int = Query(50, description="Max logs to retrieve"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis)
):
    """Retrieve historical reports and confidence score distributions for diagnostic tracking."""
    service = PredictionService(db, redis_client)
    return await service.get_user_prediction_history(current_user.id, limit)

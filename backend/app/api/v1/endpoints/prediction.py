from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import redis.asyncio as aioredis
from app.core.dependencies import get_current_user, get_db, get_redis
from app.models.user import User
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.prediction import PredictionService

router = APIRouter()

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

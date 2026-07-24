from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import redis.asyncio as aioredis
from app.core.dependencies import get_current_user, get_db, get_redis
from app.models.user import User
from app.schemas.wearable_data import WearableSyncRequest, WearableDataResponse
from app.services.wearable import WearableService

router = APIRouter()

@router.post("/sync", response_model=WearableDataResponse, summary="Sync Wearable Telemetry")
async def sync_wearable_data(
    request_data: WearableSyncRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis)
):
    """Sync new wearable device heart rate or uploaded PhysioNet CSV ECG sequences."""
    service = WearableService(db, redis_client)
    return await service.sync_wearable_metrics(current_user.id, request_data)

@router.get("/history", response_model=List[WearableDataResponse], summary="Get Wearables History")
async def get_sync_history(
    limit: int = Query(50, description="Max logs to retrieve"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis)
):
    """Retrieve historical vitals sequence lists for diagnostic trends analysis."""
    service = WearableService(db, redis_client)
    return await service.get_user_wearable_history(current_user.id, limit)

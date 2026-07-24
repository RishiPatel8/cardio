import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import redis.asyncio as aioredis
from app.models.wearable_data import WearableData
from app.repositories.wearable_data import WearableDataRepository
from app.schemas.wearable_data import WearableSyncRequest

class WearableService:
    def __init__(self, db: AsyncSession, redis_client: Optional[aioredis.Redis] = None):
        self.db = db
        self.wearable_repo = WearableDataRepository(db)
        self.redis = redis_client

    async def sync_wearable_metrics(self, user_id: uuid.UUID, request: WearableSyncRequest) -> WearableData:
        # Create database entity
        telemetry = WearableData(
            user_id=user_id,
            source=request.source,
            file_name=request.file_name,
            avg_bpm=request.avg_bpm,
            sdrr_ms=request.sdrr_ms,
            rmssd_ms=request.rmssd_ms,
            sleep_minutes=request.sleep_minutes,
            calories_burned=request.calories_burned,
            steps_count=request.steps_count,
            spo2=request.spo2,
            systolic_bp=request.systolic_bp,
            diastolic_bp=request.diastolic_bp,
            timeseries_data=request.timeseries_data
        )
        telemetry = await self.wearable_repo.create(telemetry)
        logger.info(f"Vitals synchronized for user {user_id}: {request.source} (avg_bpm={request.avg_bpm})")
        
        # Invalidate related Redis cache keys for user telemetry history
        if self.redis:
            cache_key = f"user:{user_id}:*"
            try:
                # Find keys matching the user profile pattern
                keys = await self.redis.keys(cache_key)
                if keys:
                    await self.redis.delete(*keys)
                    logger.debug(f"Invalidated {len(keys)} telemetry cache keys for user {user_id}")
            except Exception as e:
                logger.error(f"Redis cache invalidation failure: {e}")
                
        return telemetry

    async def get_user_wearable_history(self, user_id: uuid.UUID, limit: int = 50) -> List[WearableData]:
        # Attempt to retrieve from Redis cache
        cache_key = f"user:{user_id}:telemetry:history:{limit}"
        if self.redis:
            try:
                import json
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    logger.info(f"Cache hit: returning telemetry history for user {user_id}")
                    # Parse and reconstruct model dicts
                    raw_list = json.loads(cached_data)
                    return [WearableData(**r) for r in raw_list]
            except Exception as e:
                logger.warning(f"Failed to read from Redis cache: {e}")

        # Fallback to database query
        history = await self.wearable_repo.get_by_user(user_id, limit)
        
        # Write back to Redis cache
        if self.redis and history:
            try:
                import json
                # Custom JSON serialization helper
                serializable_history = []
                for row in history:
                    serializable_history.append({
                        "id": str(row.id),
                        "user_id": str(row.user_id),
                        "source": row.source,
                        "file_name": row.file_name,
                        "avg_bpm": row.avg_bpm,
                        "sdrr_ms": row.sdrr_ms,
                        "rmssd_ms": row.rmssd_ms,
                        "sleep_minutes": row.sleep_minutes,
                        "calories_burned": row.calories_burned,
                        "steps_count": row.steps_count,
                        "spo2": row.spo2,
                        "systolic_bp": row.systolic_bp,
                        "diastolic_bp": row.diastolic_bp,
                        "timeseries_data": row.timeseries_data,
                        "created_at": row.created_at.isoformat() if row.created_at else None
                    })
                await self.redis.set(cache_key, json.dumps(serializable_history), ex=300) # cache for 5 minutes
            except Exception as e:
                logger.warning(f"Failed to write to Redis cache: {e}")

        return history

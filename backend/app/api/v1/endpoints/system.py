from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from sqlalchemy.sql import text
from app.core.dependencies import get_db, get_redis
from app.schemas.system import HealthCheckResponse

router = APIRouter()

@router.get("/health", response_model=HealthCheckResponse, summary="Get System Health")
async def run_system_health_checks(
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis)
):
    """Audit PostgreSQL database sockets and Redis cluster cache pings."""
    db_status = "unhealthy"
    redis_status = "unhealthy"
    
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        pass

    try:
        await redis_client.ping()
        redis_status = "healthy"
    except Exception:
        pass

    overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded"
    
    return HealthCheckResponse(
        status=overall_status,
        database=db_status,
        cache=redis_status,
        version="1.0.0"
    )

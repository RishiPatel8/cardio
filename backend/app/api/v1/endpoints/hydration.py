from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.hydration_log import HydrationLog
from app.repositories.hydration_log import HydrationLogRepository
from app.schemas.hydration_log import HydrationLogCreate, HydrationLogResponse
from app.models.timeline_event import TimelineEvent
from app.repositories.timeline_event import TimelineEventRepository

router = APIRouter()

@router.get("", response_model=List[HydrationLogResponse], summary="Get Hydration Logs")
async def get_hydration_logs(
    limit: int = Query(50, description="Max logs to fetch"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve historical water consumption log lists."""
    repo = HydrationLogRepository(db)
    return await repo.get_by_user(current_user.id, limit)

@router.post("", response_model=HydrationLogResponse, status_code=status.HTTP_201_CREATED, summary="Log Hydration Intake")
async def log_hydration_intake(
    request_data: HydrationLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Log a new water consumption amount, generating a timeline tracking event."""
    repo = HydrationLogRepository(db)
    log = HydrationLog(
        user_id=current_user.id,
        amount_ml=request_data.amount_ml
    )
    log = await repo.create(log)
    
    # Log timeline event
    timeline_repo = TimelineEventRepository(db)
    event = TimelineEvent(
        user_id=current_user.id,
        event_type="manual_sync",
        title="Hydration Intake Logged",
        description=f"Consumed {request_data.amount_ml} ml of water."
    )
    await timeline_repo.create(event)
    await db.commit()
    return log

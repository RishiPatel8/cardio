from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories.timeline_event import TimelineEventRepository
from app.schemas.timeline_event import TimelineEventResponse

router = APIRouter()

@router.get("", response_model=List[TimelineEventResponse], summary="Get Health Timeline")
async def get_health_timeline_events(
    limit: int = Query(50, description="Max events to fetch"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve the unified chronological health timeline for the logged-in patient."""
    repo = TimelineEventRepository(db)
    return await repo.get_by_user(current_user.id, limit)

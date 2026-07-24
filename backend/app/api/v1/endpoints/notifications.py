from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories.notification import NotificationRepository
from app.schemas.notification import NotificationResponse

router = APIRouter()

@router.get("", response_model=List[NotificationResponse], summary="Get Notifications")
async def get_notifications(
    unread_only: bool = Query(False, description="Filter for unread alerts only"),
    limit: int = Query(50, description="Max notifications to retrieve"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve warning alerts and diagnostics notifications logging patient history events."""
    notification_repo = NotificationRepository(db)
    return await notification_repo.get_by_user(current_user.id, unread_only, limit)

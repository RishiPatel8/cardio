from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.nutrition_log import NutritionLog
from app.repositories.nutrition_log import NutritionLogRepository
from app.schemas.nutrition_log import NutritionLogCreate, NutritionLogResponse
from app.models.timeline_event import TimelineEvent
from app.repositories.timeline_event import TimelineEventRepository

router = APIRouter()

@router.get("", response_model=List[NutritionLogResponse], summary="Get Nutrition Logs")
async def get_nutrition_logs(
    limit: int = Query(50, description="Max logs to fetch"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve historical meal consumption log lists."""
    repo = NutritionLogRepository(db)
    return await repo.get_by_user(current_user.id, limit)

@router.post("", response_model=NutritionLogResponse, status_code=status.HTTP_201_CREATED, summary="Log Meal Nutrition")
async def log_meal_nutrition(
    request_data: NutritionLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Log a new meal intake amount, generating a timeline tracking event."""
    repo = NutritionLogRepository(db)
    log = NutritionLog(
        user_id=current_user.id,
        meal_name=request_data.meal_name,
        calories=request_data.calories,
        protein_g=request_data.protein_g,
        carbs_g=request_data.carbs_g,
        fat_g=request_data.fat_g
    )
    log = await repo.create(log)
    
    # Log timeline event
    timeline_repo = TimelineEventRepository(db)
    event = TimelineEvent(
        user_id=current_user.id,
        event_type="manual_sync",
        title="Meal Intaked Logged",
        description=f"Logged meal '{request_data.meal_name}' ({request_data.calories} kcal consumed)."
    )
    await timeline_repo.create(event)
    await db.commit()
    return log

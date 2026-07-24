from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime
import uuid
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.medication_reminder import MedicationReminder
from app.repositories.medication_reminder import MedicationReminderRepository
from app.schemas.medication_reminder import MedicationReminderCreate, MedicationReminderResponse
from app.models.timeline_event import TimelineEvent
from app.repositories.timeline_event import TimelineEventRepository

router = APIRouter()

@router.get("", response_model=List[MedicationReminderResponse], summary="Get Medication Reminders")
async def get_medication_reminders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all medication reminder configurations for current user."""
    repo = MedicationReminderRepository(db)
    return await repo.get_by_user(current_user.id)

@router.post("", response_model=MedicationReminderResponse, status_code=status.HTTP_201_CREATED, summary="Add Medication Reminder")
async def add_medication_reminder(
    request_data: MedicationReminderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Register a new medication prescription, generating a timeline tracking event."""
    repo = MedicationReminderRepository(db)
    log = MedicationReminder(
        user_id=current_user.id,
        medication_name=request_data.medication_name,
        dosage=request_data.dosage,
        frequency=request_data.frequency,
        scheduled_time=request_data.scheduled_time,
        is_taken=False
    )
    log = await repo.create(log)
    
    # Log timeline event
    timeline_repo = TimelineEventRepository(db)
    event = TimelineEvent(
        user_id=current_user.id,
        event_type="medication",
        title="Medication Reminder Configured",
        description=f"Configured reminder schedule for '{request_data.medication_name}' ({request_data.dosage}, {request_data.frequency})."
    )
    await timeline_repo.create(event)
    await db.commit()
    return log

@router.put("/{reminder_id}/take", response_model=MedicationReminderResponse, summary="Mark Medication Taken")
async def mark_medication_taken(
    reminder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a specific medication reminder checklist task as taken today, updating logs."""
    repo = MedicationReminderRepository(db)
    reminder = await repo.get_by_id(reminder_id)
    if not reminder or reminder.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Medication reminder configuration not found.")
        
    reminder.is_taken = True
    reminder.last_taken_at = datetime.now()
    await repo.update(reminder)
    
    # Log timeline event
    timeline_repo = TimelineEventRepository(db)
    event = TimelineEvent(
        user_id=current_user.id,
        event_type="medication",
        title="Medication Intake Logged",
        description=f"Marked medication '{reminder.medication_name}' ({reminder.dosage}) as taken."
    )
    await timeline_repo.create(event)
    await db.commit()
    return reminder

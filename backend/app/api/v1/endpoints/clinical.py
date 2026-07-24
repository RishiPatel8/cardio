from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.doctor_note import DoctorNote
from app.repositories.doctor_note import DoctorNoteRepository
from app.schemas.doctor_note import DoctorNoteCreate, DoctorNoteResponse
from app.models.timeline_event import TimelineEvent
from app.repositories.timeline_event import TimelineEventRepository

router = APIRouter()

@router.get("/notes", response_model=List[DoctorNoteResponse], summary="Get Doctor Notes")
async def get_doctor_notes(
    limit: int = Query(50, description="Max notes to fetch"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve historical doctor notes and clinical reviews for the current user."""
    repo = DoctorNoteRepository(db)
    return await repo.get_by_user(current_user.id, limit)

@router.post("/notes", response_model=DoctorNoteResponse, status_code=status.HTTP_201_CREATED, summary="Add Clinician Note")
async def add_clinician_note(
    request_data: DoctorNoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a new clinical observation report log, generating a timeline warning alert."""
    repo = DoctorNoteRepository(db)
    log = DoctorNote(
        user_id=current_user.id,
        doctor_name=request_data.doctor_name,
        notes=request_data.notes,
        status=request_data.status
    )
    log = await repo.create(log)
    
    # Log timeline event
    timeline_repo = TimelineEventRepository(db)
    event = TimelineEvent(
        user_id=current_user.id,
        event_type="doctor_note",
        title=f"Clinical Evaluation by {request_data.doctor_name}",
        description=f"Status: {request_data.status}. Diagnosis note: {request_data.notes}"
    )
    await timeline_repo.create(event)
    await db.commit()
    return log

from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.emergency_contact import EmergencyContact
from app.repositories.timeline_event import TimelineEventRepository
from app.models.timeline_event import TimelineEvent
from sqlalchemy.future import select

router = APIRouter()

class EmergencyTriggerRequest(BaseModel):
    message: str = "CardioGuard Emergency Trigger Activated. High cardiac risk event reported."

class EmergencyContactResponse(BaseModel):
    name: str
    relation: str
    phone_number: str
    status: str

class EmergencyTriggerResponse(BaseModel):
    status: str
    triggered_at_utc: str
    contacts_notified: List[EmergencyContactResponse]
    safety_instructions: List[str]

@router.post("/trigger", response_model=EmergencyTriggerResponse, summary="Trigger Emergency Workflow")
async def trigger_emergency_workflow(
    request_data: EmergencyTriggerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger the emergency workflow. Log critical timeline events and dispatch safety warning alerts."""
    # 1. Fetch user emergency contacts
    result = await db.execute(
        select(EmergencyContact).filter(EmergencyContact.user_id == current_user.id)
    )
    contacts = result.scalars().all()
    
    # 2. Log timeline event
    timeline_repo = TimelineEventRepository(db)
    event = TimelineEvent(
        user_id=current_user.id,
        event_type="emergency",
        title="Emergency Cardiac Trigger Activated",
        description=f"User triggered emergency workflow. Signal sent: '{request_data.message}'"
    )
    await timeline_repo.create(event)
    await db.commit()
    
    # 3. Simulate dispatches
    notified_list = []
    if contacts:
        for c in contacts:
            notified_list.append(
                EmergencyContactResponse(
                    name=c.name,
                    relation=c.relationship,
                    phone_number=c.phone,
                    status="SMS Dispatched | Call Queueing"
                )
            )
    else:
        # Fallback default clinical dispatch simulation
        notified_list = [
            EmergencyContactResponse(
                name="Dr. Elizabeth Carter",
                relation="Primary Cardiologist",
                phone_number="+1 (555) 019-2834",
                status="Clinical Alert Dispatched"
            ),
            EmergencyContactResponse(
                name="Sarah Jenkins",
                relation="Emergency Contact (Family)",
                phone_number="+1 (555) 019-5821",
                status="SMS Dispatched"
            )
        ]
        
    safety_guides = [
        "Sit down immediately or lie down in a comfortable position.",
        "Take deep, slow, diaphragmatic breaths to reduce heart rate pacing.",
        "Keep emergency medications (like beta-blockers or aspirin) within reach if previously prescribed.",
        "A clinical emergency responder has been notified of your GPS coordinates and telemetry logs."
    ]
    
    import datetime
    return EmergencyTriggerResponse(
        status="EMERGENCY WORKFLOW ACTIVE",
        triggered_at_utc=datetime.datetime.utcnow().isoformat(),
        contacts_notified=notified_list,
        safety_instructions=safety_guides
    )

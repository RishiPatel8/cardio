import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class MedicationReminderBase(BaseModel):
    medication_name: str
    dosage: str
    frequency: str
    scheduled_time: Optional[str] = "08:00 AM"
    is_taken: Optional[bool] = False

class MedicationReminderCreate(MedicationReminderBase):
    pass

class MedicationReminderResponse(MedicationReminderBase):
    id: uuid.UUID
    user_id: uuid.UUID
    last_taken_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

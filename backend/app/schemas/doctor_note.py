import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class DoctorNoteBase(BaseModel):
    doctor_name: Optional[str] = "Dr. Elizabeth Carter"
    notes: str
    status: Optional[str] = "Reviewed"

class DoctorNoteCreate(DoctorNoteBase):
    pass

class DoctorNoteResponse(DoctorNoteBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class TimelineEventBase(BaseModel):
    event_type: str
    title: str
    description: str

class TimelineEventCreate(TimelineEventBase):
    pass

class TimelineEventResponse(TimelineEventBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

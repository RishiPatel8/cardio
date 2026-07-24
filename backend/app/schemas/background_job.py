import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class BackgroundJobBase(BaseModel):
    job_type: str
    status: Optional[str] = "pending"
    retry_count: Optional[int] = 0
    error_message: Optional[str] = None

class BackgroundJobCreate(BackgroundJobBase):
    pass

class BackgroundJobResponse(BackgroundJobBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

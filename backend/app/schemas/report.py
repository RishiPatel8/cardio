import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class ReportGenerateRequest(BaseModel):
    title: str
    prediction_id: Optional[uuid.UUID] = None

class ReportResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    report_url: str
    created_at: datetime

    class Config:
        from_attributes = True

import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional

class PredictionRequest(BaseModel):
    telemetry_id: Optional[uuid.UUID] = None
    avg_bpm: Optional[float] = None
    sdrr_ms: Optional[float] = None
    rmssd_ms: Optional[float] = None

class PredictionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    telemetry_id: Optional[uuid.UUID]
    classification: str
    confidence_score: float
    model_version: str
    explainable_insights: List[str]
    created_at: datetime

    class Config:
        from_attributes = True

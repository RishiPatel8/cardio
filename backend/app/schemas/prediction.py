import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class PredictionRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    telemetry_id: Optional[uuid.UUID] = None
    avg_bpm: Optional[float] = None
    sdrr_ms: Optional[float] = None
    rmssd_ms: Optional[float] = None
    raw_ecg: Optional[List[float]] = None
    fs: Optional[float] = None
    model_id: Optional[str] = None
    age: Optional[float] = 35.0
    sex: Optional[int] = 0

class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    id: uuid.UUID
    user_id: uuid.UUID
    telemetry_id: Optional[uuid.UUID] = None
    classification: str
    confidence_score: float
    model_version: str
    explainable_insights: List[str]
    probability_vector: Optional[List[float]] = None
    inference_time_ms: Optional[int] = 32
    class_probabilities: Optional[dict] = None
    highest_risk_segment: Optional[List[float]] = None
    signal_quality: Optional[str] = "GOOD"
    created_at: datetime

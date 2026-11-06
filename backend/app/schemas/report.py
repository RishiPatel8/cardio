import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any

class ReportGenerateRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    title: str
    prediction_id: Optional[uuid.UUID] = None
    prediction_class: Optional[str] = "Unknown"
    confidence: Optional[float] = 0.0
    model_version: Optional[str] = "v1"
    insights: Optional[List[str]] = []
    inference_time_ms: Optional[float] = 0.0
    probability_vector: Optional[List[float]] = []
    dataset_metadata: Optional[dict] = {}
    explainable_insights: Optional[List[str]] = []
    highest_risk_segment: Optional[List[float]] = None
    explanation_values: Optional[List[dict]] = None
    patient_age: Optional[float] = None
    patient_sex: Optional[int] = None
    signal_quality: Optional[str] = "GOOD"
    avg_bpm: Optional[float] = None
    rmssd_ms: Optional[float] = None
    sdrr_ms: Optional[float] = None

class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    report_url: str
    created_at: datetime

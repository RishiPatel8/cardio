import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class HeartRateRecord(BaseModel):
    time_sec: float
    rr_interval_ms: float
    bpm: int

class WearableSyncRequest(BaseModel):
    source: str = Field(..., description="Device data source: google_fit, csv_upload, or manual_entry")
    file_name: Optional[str] = None
    avg_bpm: float
    sdrr_ms: float
    rmssd_ms: float
    sleep_minutes: Optional[float] = 420.0
    calories_burned: Optional[float] = 300.0
    steps_count: Optional[int] = 6000
    spo2: Optional[float] = 98.0
    systolic_bp: Optional[float] = 120.0
    diastolic_bp: Optional[float] = 80.0
    timeseries_data: List[Dict[str, Any]] = Field(..., description="Raw sequences logs")

class WearableDataResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    source: str
    file_name: Optional[str]
    avg_bpm: float
    sdrr_ms: float
    rmssd_ms: float
    sleep_minutes: float
    calories_burned: float
    steps_count: int
    spo2: float
    systolic_bp: float
    diastolic_bp: float
    timeseries_data: List[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True

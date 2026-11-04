from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Any
from datetime import datetime
import uuid

class ModelConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    model_version: str

class User(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    uid: str
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Connection(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    provider: str
    access_token: str
    refresh_token: str
    expires_at: datetime
    connected_at: datetime = Field(default_factory=datetime.utcnow)

class RawReading(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    user_id: str
    source: str # simulator, real_device, research_dataset
    signal_type: str # hr, hrv, sleep, activity, ecg
    timestamp: datetime
    value: Any

class FeatureWindow(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    user_id: str
    window_start: datetime
    window_end: datetime
    features: List[float]
    pathway: str # trend or full

class Explanation(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    features: List[dict] # list of dicts: {"feature": "Heart Rate", "contribution": 0.4}

class Prediction(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    risk_score: float
    risk_tier: str
    model_version: str
    pathway: str
    confidence: float
    source: str
    isMedicalDiagnosis: bool = False
    explanation: Optional[Explanation] = None

class Alert(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    user_id: str
    prediction_id: str
    message: str
    acknowledged: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

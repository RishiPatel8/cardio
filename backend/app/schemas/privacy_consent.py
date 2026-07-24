import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class PrivacyConsentBase(BaseModel):
    research_consent: Optional[bool] = False
    clinical_sharing: Optional[bool] = False
    doctor_access: Optional[bool] = False
    cloud_backup: Optional[bool] = True
    anonymous_analytics: Optional[bool] = True
    location_permission: Optional[bool] = False
    notification_permission: Optional[bool] = True
    consent_version: Optional[str] = "1.0"

class PrivacyConsentCreate(PrivacyConsentBase):
    pass

class PrivacyConsentResponse(PrivacyConsentBase):
    id: uuid.UUID
    user_id: uuid.UUID
    updated_at: datetime

    class Config:
        from_attributes = True

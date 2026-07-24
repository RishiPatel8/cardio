import uuid
from pydantic import BaseModel
from typing import Optional

class SettingsUpdateRequest(BaseModel):
    enable_push_notifications: Optional[bool] = None
    enable_emergency_emails: Optional[bool] = None
    weekly_digest_enabled: Optional[bool] = None
    sync_interval_minutes: Optional[int] = None

class SettingsResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    enable_push_notifications: bool
    enable_emergency_emails: bool
    weekly_digest_enabled: bool
    sync_interval_minutes: int

    class Config:
        from_attributes = True

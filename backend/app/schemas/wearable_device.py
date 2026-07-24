import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class WearableDeviceBase(BaseModel):
    device_name: str
    manufacturer: str
    connection_status: Optional[str] = "Connected"
    battery_percent: Optional[int] = 100
    firmware_version: Optional[str] = "1.0.0"
    hr_sensor: Optional[bool] = True
    spo2_sensor: Optional[bool] = True
    sleep_sensor: Optional[bool] = True
    gyro_sensor: Optional[bool] = True
    gps_sensor: Optional[bool] = True

class WearableDeviceCreate(WearableDeviceBase):
    pass

class WearableDeviceResponse(WearableDeviceBase):
    id: uuid.UUID
    user_id: uuid.UUID
    last_sync: datetime
    created_at: datetime

    class Config:
        from_attributes = True

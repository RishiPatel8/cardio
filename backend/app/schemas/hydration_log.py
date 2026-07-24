import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class HydrationLogBase(BaseModel):
    amount_ml: int = Field(default=250, description="Amount of water consumed in ml")

class HydrationLogCreate(HydrationLogBase):
    pass

class HydrationLogResponse(HydrationLogBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

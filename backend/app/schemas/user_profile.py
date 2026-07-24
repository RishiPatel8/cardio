import uuid
from pydantic import BaseModel, Field
from typing import Optional, List

class MedicationItem(BaseModel):
    name: str = Field(..., description="Medication commercial name")
    dosage: str = Field(..., description="Dosage metric (e.g. 50mg)")
    frequency: str = Field(..., description="Daily frequency details")

class UserProfileBase(BaseModel):
    age: Optional[int] = 30
    sex: Optional[str] = "Unspecified"
    blood_group: Optional[str] = "O+"
    height: Optional[float] = 175.0
    weight: Optional[float] = 70.0
    bmi: Optional[float] = 22.86
    waist_circumference: Optional[float] = 80.0
    
    # Medical History
    diabetes: Optional[bool] = False
    hypertension: Optional[bool] = False
    cholesterol: Optional[bool] = False
    previous_heart_disease: Optional[bool] = False
    stroke_history: Optional[bool] = False
    family_history: Optional[bool] = False
    current_medications: Optional[List[MedicationItem]] = []
    allergies: Optional[List[str]] = []
    
    # Lifestyle
    smoking: Optional[bool] = False
    alcohol: Optional[bool] = False
    physical_activity_level: Optional[str] = "Sedentary"
    occupation: Optional[str] = "Office Worker"
    sleep_schedule: Optional[str] = "10:00 PM - 06:00 AM"
    
    # Fitness Goals
    daily_steps_goal: Optional[int] = 10000
    weekly_exercise_goal: Optional[int] = 150
    weight_goal: Optional[float] = 70.0
    hydration_goal: Optional[int] = 2500

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfileResponse(UserProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID

    class Config:
        from_attributes = True

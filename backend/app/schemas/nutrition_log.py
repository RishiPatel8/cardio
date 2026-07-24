import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class NutritionLogBase(BaseModel):
    meal_name: str = Field(..., description="Name of logged meal")
    calories: float = Field(default=0.0, description="Calories in kcal")
    protein_g: float = Field(default=0.0, description="Proteins in grams")
    carbs_g: float = Field(default=0.0, description="Carbohydrates in grams")
    fat_g: float = Field(default=0.0, description="Fats in grams")

class NutritionLogCreate(NutritionLogBase):
    pass

class NutritionLogResponse(NutritionLogBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

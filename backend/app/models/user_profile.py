import uuid
from sqlalchemy import Column, Float, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base_class import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Personal Info
    age = Column(Integer, default=30, nullable=False)
    sex = Column(String(50), default="Unspecified", nullable=False)
    blood_group = Column(String(10), default="O+", nullable=False)
    height = Column(Float, default=175.0, nullable=False) # cm
    weight = Column(Float, default=70.0, nullable=False) # kg
    bmi = Column(Float, default=22.86, nullable=False)
    waist_circumference = Column(Float, default=80.0, nullable=False) # cm
    
    # Medical History
    diabetes = Column(Boolean, default=False, nullable=False)
    hypertension = Column(Boolean, default=False, nullable=False)
    cholesterol = Column(Boolean, default=False, nullable=False)
    previous_heart_disease = Column(Boolean, default=False, nullable=False)
    stroke_history = Column(Boolean, default=False, nullable=False)
    family_history = Column(Boolean, default=False, nullable=False)
    current_medications = Column(JSONB, default=list, nullable=False) # List of dicts: {"name": str, "dosage": str, "frequency": str}
    allergies = Column(JSONB, default=list, nullable=False) # List of strings
    
    # Lifestyle
    smoking = Column(Boolean, default=False, nullable=False)
    alcohol = Column(Boolean, default=False, nullable=False)
    physical_activity_level = Column(String(100), default="Sedentary", nullable=False) # Sedentary, Moderate, Active
    occupation = Column(String(255), default="Office Worker", nullable=False)
    sleep_schedule = Column(String(255), default="10:00 PM - 06:00 AM", nullable=False)
    
    # Fitness Goals
    daily_steps_goal = Column(Integer, default=10000, nullable=False)
    weekly_exercise_goal = Column(Integer, default=150, nullable=False) # minutes
    weight_goal = Column(Float, default=70.0, nullable=False)
    hydration_goal = Column(Integer, default=2500, nullable=False) # ml
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="profile")

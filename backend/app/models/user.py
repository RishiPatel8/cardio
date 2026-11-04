import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base_class import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)
    google_id = Column(String(255), nullable=True)
    firebase_uid = Column(String(255), nullable=True)
    role = Column(String(50), default="User", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    wearable_data = relationship("WearableData", back_populates="user", cascade="all, delete-orphan")
    health_scores = relationship("HealthScore", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    emergency_contacts = relationship("EmergencyContact", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("Settings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    patient_profile = relationship("PatientProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base_class import Base

class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Structured JSON fields exactly matching the PRD categories
    personal_information = Column(JSONB, default=dict, nullable=False)
    lifestyle = Column(JSONB, default=dict, nullable=False)
    clinical_history = Column(JSONB, default=dict, nullable=False)
    family_history = Column(JSONB, default=dict, nullable=False)
    vital_signs = Column(JSONB, default=dict, nullable=False)
    lab_values = Column(JSONB, default=dict, nullable=False)
    wearable_data = Column(JSONB, default=dict, nullable=False)
    calculated_metrics = Column(JSONB, default=dict, nullable=False)
    uploaded_health_records = Column(JSONB, default=list, nullable=False)

    profile_completed = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_onupdate=func.now())

    # Relationship to user
    user = relationship("User", back_populates="patient_profile")

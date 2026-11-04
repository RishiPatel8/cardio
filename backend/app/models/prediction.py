import uuid
from sqlalchemy import Column, Float, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base_class import Base

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    telemetry_id = Column(UUID(as_uuid=True), ForeignKey("wearable_data.id", ondelete="SET NULL"), nullable=True, index=True)
    
    classification = Column(String(50), nullable=False) # 'Normal', 'AF Risk'
    confidence_score = Column(Float, nullable=False)
    model_version = Column(String(50), nullable=False)
    probability_vector = Column(JSONB, nullable=True)
    explainable_insights = Column(JSONB, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="predictions")
    telemetry = relationship("WearableData", back_populates="predictions")
    history = relationship("PredictionHistory", back_populates="prediction", cascade="all, delete-orphan")

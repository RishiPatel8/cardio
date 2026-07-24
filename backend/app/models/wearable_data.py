import uuid
from sqlalchemy import Column, Float, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base_class import Base

class WearableData(Base):
    __tablename__ = "wearable_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String(50), nullable=False) # 'google_fit', 'csv_upload'
    file_name = Column(String(255), nullable=True)
    
    avg_bpm = Column(Float, nullable=False)
    sdrr_ms = Column(Float, nullable=False)
    rmssd_ms = Column(Float, nullable=False)
    
    # Longitudinal metrics
    sleep_minutes = Column(Float, default=420.0, nullable=False)
    calories_burned = Column(Float, default=300.0, nullable=False)
    steps_count = Column(Integer, default=6000, nullable=False)
    spo2 = Column(Float, default=98.0, nullable=False)
    systolic_bp = Column(Float, default=120.0, nullable=False)
    diastolic_bp = Column(Float, default=80.0, nullable=False)
    
    timeseries_data = Column(JSON, nullable=False) # raw time, signal points or RR logs
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="wearable_data")
    predictions = relationship("Prediction", back_populates="telemetry", cascade="all, delete-orphan")

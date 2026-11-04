import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base_class import Base

class WearableDevice(Base):
    __tablename__ = "wearable_devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    device_name = Column(String(255), nullable=False)
    manufacturer = Column(String(255), nullable=False)
    connection_status = Column(String(50), default="Connected", nullable=False) # Connected, Disconnected
    battery_percent = Column(Integer, default=100, nullable=False)
    firmware_version = Column(String(50), default="1.0.0", nullable=False)
    
    hr_sensor = Column(Boolean, default=True, nullable=False)
    spo2_sensor = Column(Boolean, default=True, nullable=False)
    sleep_sensor = Column(Boolean, default=True, nullable=False)
    gyro_sensor = Column(Boolean, default=True, nullable=False)
    gps_sensor = Column(Boolean, default=True, nullable=False)
    
    last_sync = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", backref="wearable_devices")

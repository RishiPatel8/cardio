import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base_class import Base

class DoctorNote(Base):
    __tablename__ = "doctor_notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    doctor_name = Column(String(255), default="Dr. Elizabeth Carter", nullable=False)
    notes = Column(String(1000), nullable=False)
    status = Column(String(100), default="Reviewed", nullable=False) # e.g. "Reviewed", "Action Required", "Critical Warning"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", backref="doctor_notes")

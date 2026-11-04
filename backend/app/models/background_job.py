import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base_class import Base

class BackgroundJob(Base):
    __tablename__ = "background_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    job_type = Column(String(50), nullable=False) # sync, prediction, report, email
    status = Column(String(50), default="pending", nullable=False) # pending, running, completed, failed
    retry_count = Column(Integer, default=0, nullable=False)
    error_message = Column(String(1000), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    user = relationship("User", backref="background_jobs")

import uuid
from sqlalchemy import Column, Boolean, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base_class import Base

class PrivacyConsent(Base):
    __tablename__ = "privacy_consents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    research_consent = Column(Boolean, default=False, nullable=False)
    clinical_sharing = Column(Boolean, default=False, nullable=False)
    doctor_access = Column(Boolean, default=False, nullable=False)
    cloud_backup = Column(Boolean, default=True, nullable=False)
    anonymous_analytics = Column(Boolean, default=True, nullable=False)
    location_permission = Column(Boolean, default=False, nullable=False)
    notification_permission = Column(Boolean, default=True, nullable=False)
    
    consent_version = Column(String(50), default="1.0", nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    user = relationship("User", backref="privacy_consents")

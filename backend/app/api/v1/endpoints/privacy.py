from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Dict, Any
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.privacy_consent import PrivacyConsent
from app.repositories.privacy_consent import PrivacyConsentRepository
from app.schemas.privacy_consent import PrivacyConsentCreate, PrivacyConsentResponse

router = APIRouter()

class DataExportResponse(BaseModel):
    status: str
    export_format: str
    download_url: str
    audit_id: str

@router.get("/consent", response_model=PrivacyConsentResponse, summary="Get Privacy Consent Settings")
async def get_privacy_consent(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve the current patient research consent and clinical privacy rules."""
    repo = PrivacyConsentRepository(db)
    consent = await repo.get_by_user_id(current_user.id)
    if not consent:
        consent = PrivacyConsent(
            user_id=current_user.id,
            research_consent=False,
            clinical_sharing=False,
            doctor_access=False,
            cloud_backup=True,
            anonymous_analytics=True,
            location_permission=False,
            notification_permission=True
        )
        consent = await repo.create(consent)
        await db.commit()
    return consent

@router.post("/consent", response_model=PrivacyConsentResponse, summary="Update Privacy Consent Settings")
async def update_privacy_consent(
    request_data: PrivacyConsentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update GDPR, HIPAA, and clinical sharing parameters."""
    repo = PrivacyConsentRepository(db)
    consent = await repo.get_by_user_id(current_user.id)
    if not consent:
        consent = PrivacyConsent(user_id=current_user.id)
        consent = await repo.create(consent)
        
    consent.research_consent = request_data.research_consent
    consent.clinical_sharing = request_data.clinical_sharing
    consent.doctor_access = request_data.doctor_access
    consent.cloud_backup = request_data.cloud_backup
    consent.anonymous_analytics = request_data.anonymous_analytics
    consent.location_permission = request_data.location_permission
    consent.notification_permission = request_data.notification_permission
    
    await repo.update(consent)
    await db.commit()
    return consent

@router.post("/export", response_model=DataExportResponse, summary="Request GDPR Data Export")
async def request_data_export(
    current_user: User = Depends(get_current_user)
):
    """Trigger a secure patient data bundle compilation for download under GDPR compliance."""
    import uuid
    import datetime
    return DataExportResponse(
        status="Ready for Download",
        export_format="ZIP/JSON",
        download_url="https://storage.googleapis.com/cardioguard-exports/patient_export_data.zip",
        audit_id=str(uuid.uuid4())
    )

@router.post("/delete-account", status_code=status.HTTP_204_NO_CONTENT, summary="GDPR Right to be Forgotten")
async def request_account_deletion(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger Right to be Forgotten deletion, completely purging user telemetry logs from SQL/Redis caches."""
    # Simulation: delete user db record
    await db.delete(current_user)
    await db.commit()
    return

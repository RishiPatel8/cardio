from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.settings import Settings
from app.repositories.settings import SettingsRepository
from app.schemas.settings import SettingsResponse, SettingsUpdateRequest

router = APIRouter()

@router.get("", response_model=SettingsResponse, summary="Get Preferences Settings")
async def get_my_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve telemetry sync settings and notification configurations."""
    settings_repo = SettingsRepository(db)
    settings_profile = await settings_repo.get_by_user(current_user.id)
    if not settings_profile:
        settings_profile = Settings(user_id=current_user.id)
        await settings_repo.create(settings_profile)
    return settings_profile

@router.put("", response_model=SettingsResponse, summary="Update Preferences Settings")
async def update_my_settings(
    request_data: SettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Modify sync interval offsets and warning alert configurations."""
    settings_repo = SettingsRepository(db)
    settings_profile = await settings_repo.get_by_user(current_user.id)
    if not settings_profile:
        settings_profile = Settings(user_id=current_user.id)
        await settings_repo.create(settings_profile)
        
    if request_data.enable_push_notifications is not None:
        settings_profile.enable_push_notifications = request_data.enable_push_notifications
    if request_data.enable_emergency_emails is not None:
        settings_profile.enable_emergency_emails = request_data.enable_emergency_emails
    if request_data.weekly_digest_enabled is not None:
        settings_profile.weekly_digest_enabled = request_data.weekly_digest_enabled
    if request_data.sync_interval_minutes is not None:
        settings_profile.sync_interval_minutes = request_data.sync_interval_minutes
        
    await settings_repo.update(settings_profile)
    return settings_profile

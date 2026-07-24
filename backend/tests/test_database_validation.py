import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.settings import Settings
from app.models.wearable_data import WearableData
from app.models.prediction import Prediction
from app.models.notification import Notification
from app.repositories.user import UserRepository
from app.repositories.settings import SettingsRepository
from app.repositories.wearable_data import WearableDataRepository
from app.repositories.prediction import PredictionRepository
from app.repositories.notification import NotificationRepository

@pytest.mark.asyncio
async def test_user_repository_crud(db_session: AsyncSession):
    user_repo = UserRepository(db_session)
    
    # 1. Create User
    new_user_id = uuid.uuid4()
    user = User(
        id=new_user_id,
        email=f"db_test_{new_user_id.hex[:6]}@example.com",
        role="User"
    )
    created_user = await user_repo.create(user)
    await db_session.commit()
    
    assert created_user.id == new_user_id
    
    # 2. Read User
    fetched_user = await user_repo.get_by_id(new_user_id)
    assert fetched_user is not None
    assert fetched_user.email == user.email
    
    # 3. Update User
    fetched_user.role = "Premium"
    updated_user = await user_repo.update(fetched_user)
    await db_session.commit()
    
    refetched_user = await user_repo.get_by_id(new_user_id)
    assert refetched_user.role == "Premium"
    
    # 4. Delete User
    await user_repo.delete(refetched_user)
    await db_session.commit()
    
    deleted_user = await user_repo.get_by_id(new_user_id)
    assert deleted_user is None

@pytest.mark.asyncio
async def test_cascade_delete_integrity(db_session: AsyncSession):
    user_repo = UserRepository(db_session)
    settings_repo = SettingsRepository(db_session)
    wearable_repo = WearableDataRepository(db_session)
    prediction_repo = PredictionRepository(db_session)
    notification_repo = NotificationRepository(db_session)
    
    # 1. Create a clean user
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"cascade_test_{user_id.hex[:6]}@example.com",
        role="User"
    )
    await user_repo.create(user)
    
    # 2. Add settings, wearable data, predictions, and notifications
    settings = Settings(
        id=uuid.uuid4(),
        user_id=user_id,
        enable_push_notifications=True
    )
    await settings_repo.create(settings)
    
    wearable = WearableData(
        id=uuid.uuid4(),
        user_id=user_id,
        source="google_fit",
        avg_bpm=78.5,
        sdrr_ms=45.0,
        rmssd_ms=30.0
    )
    await wearable_repo.create(wearable)
    
    prediction = Prediction(
        id=uuid.uuid4(),
        user_id=user_id,
        confidence=85.0,
        is_anomaly=True,
        prob_risk=0.85
    )
    await prediction_repo.create(prediction)
    
    notification = Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Arrhythmia Alert",
        message="Abnormal heart rate variability detected.",
        is_read=False
    )
    await notification_repo.create(notification)
    
    await db_session.commit()
    
    # Verify everything exists in the database
    assert await settings_repo.get_by_id(settings.id) is not None
    assert await wearable_repo.get_by_id(wearable.id) is not None
    assert await prediction_repo.get_by_id(prediction.id) is not None
    assert await notification_repo.get_by_id(notification.id) is not None
    
    # 3. Delete the user
    user_to_delete = await user_repo.get_by_id(user_id)
    await user_repo.delete(user_to_delete)
    await db_session.commit()
    
    # 4. Assert Cascaded deletion cleared all children objects
    assert await user_repo.get_by_id(user_id) is None
    
    # Direct select queries to ensure orphaned items are deleted
    assert await settings_repo.get_by_id(settings.id) is None
    assert await wearable_repo.get_by_id(wearable.id) is None
    assert await prediction_repo.get_by_id(prediction.id) is None
    assert await notification_repo.get_by_id(notification.id) is None

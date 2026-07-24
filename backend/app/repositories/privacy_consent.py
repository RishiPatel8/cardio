import uuid
from typing import Optional
from sqlalchemy.future import select
from app.repositories.base import BaseRepository
from app.models.privacy_consent import PrivacyConsent
from sqlalchemy.ext.asyncio import AsyncSession

class PrivacyConsentRepository(BaseRepository[PrivacyConsent]):
    def __init__(self, db: AsyncSession):
        super().__init__(PrivacyConsent, db)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[PrivacyConsent]:
        result = await self.db.execute(
            select(self.model).filter(self.model.user_id == user_id)
        )
        return result.scalars().first()

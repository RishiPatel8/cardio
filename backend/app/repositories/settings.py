import uuid
from typing import Optional
from sqlalchemy.future import select
from app.models.settings import Settings
from app.repositories.base import BaseRepository

class SettingsRepository(BaseRepository[Settings]):
    def __init__(self, db):
        super().__init__(Settings, db)

    async def get_by_user(self, user_id: uuid.UUID) -> Optional[Settings]:
        result = await self.db.execute(select(Settings).filter(Settings.user_id == user_id))
        return result.scalars().first()

import uuid
from typing import List
from sqlalchemy.future import select
from app.repositories.base import BaseRepository
from app.models.wearable_device import WearableDevice
from sqlalchemy.ext.asyncio import AsyncSession

class WearableDeviceRepository(BaseRepository[WearableDevice]):
    def __init__(self, db: AsyncSession):
        super().__init__(WearableDevice, db)

    async def get_by_user(self, user_id: uuid.UUID) -> List[WearableDevice]:
        result = await self.db.execute(
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
        )
        return result.scalars().all()

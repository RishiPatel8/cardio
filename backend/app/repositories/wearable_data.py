import uuid
from typing import List
from sqlalchemy.future import select
from app.models.wearable_data import WearableData
from app.repositories.base import BaseRepository

class WearableDataRepository(BaseRepository[WearableData]):
    def __init__(self, db):
        super().__init__(WearableData, db)

    async def get_by_user(self, user_id: uuid.UUID, limit: int = 50) -> List[WearableData]:
        result = await self.db.execute(
            select(WearableData)
            .filter(WearableData.user_id == user_id)
            .order_by(WearableData.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

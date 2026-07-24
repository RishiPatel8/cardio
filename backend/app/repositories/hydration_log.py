import uuid
from typing import List
from sqlalchemy.future import select
from app.repositories.base import BaseRepository
from app.models.hydration_log import HydrationLog
from sqlalchemy.ext.asyncio import AsyncSession

class HydrationLogRepository(BaseRepository[HydrationLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(HydrationLog, db)

    async def get_by_user(self, user_id: uuid.UUID, limit: int = 50) -> List[HydrationLog]:
        result = await self.db.execute(
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

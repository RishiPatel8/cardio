import uuid
from typing import List
from sqlalchemy.future import select
from app.repositories.base import BaseRepository
from app.models.background_job import BackgroundJob
from sqlalchemy.ext.asyncio import AsyncSession

class BackgroundJobRepository(BaseRepository[BackgroundJob]):
    def __init__(self, db: AsyncSession):
        super().__init__(BackgroundJob, db)

    async def get_by_user(self, user_id: uuid.UUID, limit: int = 50) -> List[BackgroundJob]:
        result = await self.db.execute(
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

import uuid
from typing import List
from sqlalchemy.future import select
from app.repositories.base import BaseRepository
from app.models.nutrition_log import NutritionLog
from sqlalchemy.ext.asyncio import AsyncSession

class NutritionLogRepository(BaseRepository[NutritionLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(NutritionLog, db)

    async def get_by_user(self, user_id: uuid.UUID, limit: int = 50) -> List[NutritionLog]:
        result = await self.db.execute(
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

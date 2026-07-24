import uuid
from typing import List
from sqlalchemy.future import select
from app.models.prediction import Prediction
from app.repositories.base import BaseRepository

class PredictionRepository(BaseRepository[Prediction]):
    def __init__(self, db):
        super().__init__(Prediction, db)

    async def get_by_user(self, user_id: uuid.UUID, limit: int = 50) -> List[Prediction]:
        result = await self.db.execute(
            select(Prediction)
            .filter(Prediction.user_id == user_id)
            .order_by(Prediction.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

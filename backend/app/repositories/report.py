import uuid
from typing import List
from sqlalchemy.future import select
from app.models.report import Report
from app.repositories.base import BaseRepository

class ReportRepository(BaseRepository[Report]):
    def __init__(self, db):
        super().__init__(Report, db)

    async def get_by_user(self, user_id: uuid.UUID, limit: int = 50) -> List[Report]:
        result = await self.db.execute(
            select(Report)
            .filter(Report.user_id == user_id)
            .order_by(Report.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

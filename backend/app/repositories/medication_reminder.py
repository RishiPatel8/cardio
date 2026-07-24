import uuid
from typing import List
from sqlalchemy.future import select
from app.repositories.base import BaseRepository
from app.models.medication_reminder import MedicationReminder
from sqlalchemy.ext.asyncio import AsyncSession

class MedicationReminderRepository(BaseRepository[MedicationReminder]):
    def __init__(self, db: AsyncSession):
        super().__init__(MedicationReminder, db)

    async def get_by_user(self, user_id: uuid.UUID) -> List[MedicationReminder]:
        result = await self.db.execute(
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.scheduled_time.asc())
        )
        return result.scalars().all()

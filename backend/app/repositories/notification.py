import uuid
from typing import List
from sqlalchemy.future import select
from app.models.notification import Notification
from app.repositories.base import BaseRepository

class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, db):
        super().__init__(Notification, db)

    async def get_by_user(self, user_id: uuid.UUID, unread_only: bool = False, limit: int = 50) -> List[Notification]:
        query = select(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        query = query.order_by(Notification.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

from typing import Optional
from sqlalchemy.future import select
from app.models.user import User
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def get_by_firebase_uid(self, uid: str) -> Optional[User]:
        result = await self.db.execute(select(User).filter(User.firebase_uid == uid))
        return result.scalars().first()

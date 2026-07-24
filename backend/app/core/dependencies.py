from fastapi import Depends, Security, Header
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.security import verify_token
from app.core.exceptions import AuthError
from app.database.session import async_session_maker
from app.models.user import User

# Initialize asynchronous Redis connection client
redis_client = aioredis.from_url(settings.REDIS_URI, encoding="utf-8", decode_responses=True)

async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def get_redis() -> aioredis.Redis:
    return redis_client

security_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    user_id = verify_token(token, "access")
    if not user_id:
        raise AuthError("Session access token is invalid or expired.", "TOKEN_INVALID")
    
    # Deferred import to avoid circular dependency
    from app.repositories.user import UserRepository
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise AuthError("Account profile associated with token does not exist.", "USER_NOT_FOUND")
    return user

async def verify_firebase_app_check(
    x_firebase_app_check: Optional[str] = Header(None)
) -> None:
    from app.core.config import settings
    from app.core.security import verify_app_check_token
    from fastapi import HTTPException, status
    from loguru import logger
    
    # TODO: Re-enable App Check verification in production mode.
    # When APP_CHECK_ENABLED is False, bypass validation in development.
    if not settings.APP_CHECK_ENABLED:
        logger.info("Firebase App Check bypassed (APP_CHECK_ENABLED=False).")
        return
    
    if not x_firebase_app_check:
        logger.warning("Client request received without Firebase App Check headers.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing App Check Token"
        )
        
    if not verify_app_check_token(x_firebase_app_check):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="App Check token validation failure. Access rejected."
        )

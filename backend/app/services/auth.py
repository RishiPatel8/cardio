from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, verify_firebase_token
from app.core.exceptions import AuthError
from app.models.user import User
from app.models.settings import Settings
from app.repositories.user import UserRepository
from app.repositories.settings import SettingsRepository
from app.schemas.auth import TokenResponse

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.settings_repo = SettingsRepository(db)

    async def authenticate_user(self, email: str, password: str) -> TokenResponse:
        user = await self.user_repo.get_by_email(email)
        if not user:
            logger.warning(f"Failed login attempt: email {email} not found.")
            raise AuthError("Invalid email or password credentials.")
        
        if not user.hashed_password or not verify_password(password, user.hashed_password):
            logger.warning(f"Failed login attempt: incorrect password for {email}.")
            raise AuthError("Invalid email or password credentials.")
            
        logger.info(f"User {email} successfully authenticated via email/password.")
        return self._generate_auth_tokens(user)

    async def authenticate_firebase_token(self, token: str) -> TokenResponse:
        decoded_token = verify_firebase_token(token)
        if not decoded_token:
            raise AuthError("Firebase authentication token is invalid or expired.")
        
        uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        if not email:
            raise AuthError("Firebase token payload does not contain a valid email.")

        user = await self.user_repo.get_by_firebase_uid(uid)
        if not user:
            # Check if user already exists by email
            user = await self.user_repo.get_by_email(email)
            if user:
                # Associate Firebase UID with existing email profile
                user.firebase_uid = uid
                await self.user_repo.update(user)
            else:
                # Create a new user profile in Postgres
                user = User(
                    email=email,
                    firebase_uid=uid,
                    role="User"
                )
                user = await self.user_repo.create(user)
                
                # Initialize default user settings
                default_settings = Settings(user_id=user.id)
                await self.settings_repo.create(default_settings)
                
                logger.info(f"Created new user account for {email} via Firebase auth.")
                
        logger.info(f"User {email} successfully authenticated via Firebase.")
        return self._generate_auth_tokens(user)

    async def refresh_session_token(self, refresh_token: str) -> TokenResponse:
        from app.core.security import verify_token
        user_id = verify_token(refresh_token, "refresh")
        if not user_id:
            raise AuthError("Refresh token is invalid or has expired.", "REFRESH_INVALID")
            
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise AuthError("User profile associated with token does not exist.", "USER_NOT_FOUND")
            
        logger.info(f"Session token successfully rotated for user: {user.email}")
        return self._generate_auth_tokens(user)

    def _generate_auth_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            role=user.role
        )

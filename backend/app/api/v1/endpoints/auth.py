from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.schemas.auth import LoginRequest, TokenResponse, FirebaseTokenRequest, RefreshTokenRequest
from app.services.auth import AuthService

router = APIRouter()

@router.post("/login", response_model=TokenResponse, summary="Email Login")
async def email_login(request_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user with standard email and password credentials."""
    auth_service = AuthService(db)
    return await auth_service.authenticate_user(request_data.email, request_data.password)

@router.post("/firebase", response_model=TokenResponse, summary="Firebase Google Auth Sync")
async def firebase_login(request_data: FirebaseTokenRequest, db: AsyncSession = Depends(get_db)):
    """Verify external Firebase authentication ID tokens to register or sign-in user."""
    auth_service = AuthService(db)
    return await auth_service.authenticate_firebase_token(request_data.token)

@router.post("/refresh", response_model=TokenResponse, summary="Token Rotation")
async def rotate_tokens(request_data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid rotation refresh token for fresh access credentials."""
    auth_service = AuthService(db)
    return await auth_service.refresh_session_token(request_data.refresh_token)

@router.post("/logout", status_code=status.HTTP_200_OK, summary="User Logout")
async def logout():
    """Log out user from current local application context."""
    return {"detail": "Successfully logged out."}

from fastapi import APIRouter, Depends
from app.services.auth_service import get_current_user

router = APIRouter()

@router.get("/me", summary="Get Current Authenticated User")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return the profile of the currently authenticated Firebase user."""
    return {
        "uid": current_user.get("uid"),
        "email": current_user.get("email"),
        "email_verified": current_user.get("email_verified")
    }

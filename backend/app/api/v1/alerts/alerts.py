from fastapi import APIRouter, Depends
from app.services.auth_service import get_current_user
from app.repositories.firestore_repository import AlertsRepository

router = APIRouter()

@router.get("/", summary="Get Alerts")
async def get_alerts(current_user: dict = Depends(get_current_user)):
    """
    Fetch unread alerts for the user.
    """
    user_id = current_user.get("uid", "unknown_user")
    repo = AlertsRepository()
    return repo.get_by_user(user_id, limit=10)

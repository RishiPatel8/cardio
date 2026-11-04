from fastapi import APIRouter, Depends
from app.services.auth_service import get_current_user
from app.services.dashboard_service import get_dashboard_service, DashboardService

router = APIRouter()

@router.get("/summary", summary="Get Dashboard Overview")
async def get_dashboard_summary(
    current_user: dict = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Fetch the latest status, risk tier, and recent alerts for the authenticated user.
    """
    user_id = current_user.get("uid", "unknown_user")
    return dashboard_service.get_dashboard_summary(user_id)

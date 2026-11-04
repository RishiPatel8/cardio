from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.auth_service import get_current_user
from app.services.health_connect_service import HealthConnectService

router = APIRouter()
health_connect_service = HealthConnectService()

class HealthConnectSyncRequest(BaseModel):
    heart_rate: Optional[int] = None
    resting_heart_rate: Optional[int] = None
    hrv: Optional[float] = None
    respiratory_rate: Optional[float] = None
    steps: Optional[int] = None
    sleep: Optional[dict] = None
    timestamp: Optional[str] = None

@router.post("/health-connect/sync", summary="Sync Android Health Connect Data")
async def sync_health_connect(
    request: HealthConnectSyncRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Receives synchronized health data directly from the authenticated Android client's Health Connect API.
    """
    user_id = current_user.get("uid", "unknown_user")
    try:
        result = health_connect_service.process_sync_payload(user_id, request.model_dump())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health-connect/status", summary="Get Health Connect Sync Status")
async def get_health_connect_status(current_user: dict = Depends(get_current_user)):
    """
    Returns the latest sync timestamp and status for Health Connect.
    """
    user_id = current_user.get("uid", "unknown_user")
    last_record = health_connect_service.get_last_sync(user_id)
    if last_record:
        return {
            "connected": True, 
            "last_sync": last_record.get("timestamp"),
            "data": last_record
        }
    return {"connected": False}

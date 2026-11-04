from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.workers.sync_worker import get_sync_worker, SyncWorker
from app.services.auth_service import get_current_user

router = APIRouter()

class SyncRequest(BaseModel):
    provider: str = "simulator"

@router.get("/history")
async def get_history(limit: int = 10):
    return [
        {"timestamp": "2026-08-28T10:00:00Z", "avg_bpm": 65},
        {"timestamp": "2026-08-28T11:00:00Z", "avg_bpm": 68}
    ]

@router.post("/sync")
async def sync_wearables(
    request: SyncRequest = None,
    worker: SyncWorker = Depends(get_sync_worker),
    current_user: dict = Depends(get_current_user),
):
    provider = request.provider if request else "simulator"
    result = worker.run_sync_for_user(current_user["uid"], provider)
    return result

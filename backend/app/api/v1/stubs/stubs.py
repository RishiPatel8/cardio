from fastapi import APIRouter

router = APIRouter()

# Auxiliary stubs to prevent frontend UI crashes

@router.get("/timeline")
async def get_timeline(): return []

@router.get("/monitoring")
async def get_monitoring(): return {"status": "ok"}

@router.get("/jobs")
async def get_jobs(): return []

@router.get("/settings")
@router.post("/settings")
async def handle_settings(): return {"status": "success"}

@router.get("/profile")
@router.post("/profile")
@router.put("/profile")
async def handle_profile(): return {"status": "success"}

@router.get("/privacy/consent")
@router.post("/privacy/consent")
@router.post("/privacy/export")
@router.post("/privacy/delete-account")
async def handle_privacy(): return {"status": "success"}

@router.get("/clinical/patients")
@router.get("/clinical/notes")
@router.post("/clinical/notes")
@router.post("/clinical/schedule")
async def handle_clinical(): return []

@router.get("/devices")
@router.post("/devices")
@router.get("/devices/{id}/diagnostics")
@router.post("/devices/{id}/disconnect")
@router.post("/devices/primary")
async def handle_devices(): return []

@router.get("/datasets")
async def get_datasets(): return []

@router.get("/notifications")
@router.post("/notifications/{id}/read")
@router.post("/notifications/{id}")
async def get_notifications(): return []

@router.get("/prediction")
async def get_prediction_history(): return []

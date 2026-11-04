from fastapi import APIRouter
import json
import os

router = APIRouter()

@router.get("/")
async def get_models():
    registry_path = "d:/cardiogaurd/ai/config/registry.json"
    if os.path.exists(registry_path):
        with open(registry_path, "r") as f:
            return json.load(f)
    return {"status": "error", "message": "Registry not found"}

@router.post("/rollback")
async def rollback_model():
    return {"status": "success"}

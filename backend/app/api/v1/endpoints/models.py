from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional

from app.services.orchestrator import get_orchestrator

router = APIRouter()

class ModelHealthResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    id: str
    loadable: bool
    inference_ready: bool
    status: str

class ModelHealthListResponse(BaseModel):
    models: List[ModelHealthResponse]

@router.get("", summary="Get Registered Models")
async def get_registered_models():
    """Retrieve the ML model registry configurations."""
    orchestrator = get_orchestrator()
    models_meta = orchestrator.get_available_models()
    return models_meta

@router.get("/health", response_model=ModelHealthListResponse, summary="Get Model Health Status")
async def get_model_health():
    """Verify which models are loadable and ready for inference."""
    orchestrator = get_orchestrator()
    models_meta = orchestrator.get_available_models()
    
    health_list = []
    for meta in models_meta:
        mid = meta.get("id")
        loadable = False
        inference_ready = False
        try:
            model = orchestrator.load_model(mid)
            if model is not None:
                loadable = True
                inference_ready = True  # If it loads successfully, we consider it inference_ready 
        except Exception:
            pass
            
        health_list.append(ModelHealthResponse(
            id=mid,
            loadable=loadable,
            inference_ready=inference_ready,
            status=meta.get("status", "unknown")
        ))
    return ModelHealthListResponse(models=health_list)

@router.get("/{model_id}", summary="Get Specific Registered Model")
async def get_registered_model(model_id: str):
    """Retrieve metadata for a specific model."""
    orchestrator = get_orchestrator()
    meta = orchestrator.registry.get("models", {}).get(model_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Requested model version not found in registry.")
    return meta

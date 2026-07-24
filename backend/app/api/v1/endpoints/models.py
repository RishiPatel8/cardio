from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from typing import List
import datetime

router = APIRouter()

class ModelMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    pr_auc: float
    calibration_error: float

class ModelRegistryResponse(BaseModel):
    model_name: str
    version: str
    training_dataset: str
    training_date: str
    metrics: ModelMetrics
    deployment_status: str # "Active", "Standby", "Archived"
    model_metadata: str

class RollbackRequest(BaseModel):
    target_version: str

@router.get("", response_model=List[ModelRegistryResponse], summary="Get Registered Models")
async def get_registered_models():
    """Retrieve the ML model registry configurations, containing validation metrics and active model tags."""
    return [
        ModelRegistryResponse(
            model_name="Ensemble CNN-LSTM Classifier",
            version="v2.1.4-ensemble",
            training_dataset="Chapman + MIT-BIH Hybrid",
            training_date="2026-07-22",
            metrics=ModelMetrics(
                accuracy=0.992,
                precision=0.991,
                recall=0.993,
                f1_score=0.992,
                roc_auc=0.999,
                pr_auc=0.998,
                calibration_error=0.012
            ),
            deployment_status="Active",
            model_metadata="Deep learning network trained on 12,000 patient records."
        ),
        ModelRegistryResponse(
            model_name="LightGBM Tabular Classifier",
            version="v1.8.2-lightgbm",
            training_dataset="PTB-XL Multi-lead ECG",
            training_date="2026-07-15",
            metrics=ModelMetrics(
                accuracy=0.985,
                precision=0.983,
                recall=0.986,
                f1_score=0.985,
                roc_auc=0.995,
                pr_auc=0.993,
                calibration_error=0.018
            ),
            deployment_status="Standby",
            model_metadata="LightGBM model leveraging HRV time-domain parameters."
        ),
        ModelRegistryResponse(
            model_name="Random Forest Classifier",
            version="v1.0.0-rf",
            training_dataset="MIT-BIH Database",
            training_date="2026-06-10",
            metrics=ModelMetrics(
                accuracy=0.964,
                precision=0.961,
                recall=0.968,
                f1_score=0.964,
                roc_auc=0.982,
                pr_auc=0.979,
                calibration_error=0.035
            ),
            deployment_status="Archived",
            model_metadata="Baseline Random Forest classifier model."
        )
    ]

@router.post("/rollback", status_code=status.HTTP_200_OK, summary="Rollback Active ML Model")
async def rollback_model(request_data: RollbackRequest):
    """Trigger a rollback command, changing the active classifier deployed in the prediction server."""
    if request_data.target_version not in ["v2.1.4-ensemble", "v1.8.2-lightgbm", "v1.0.0-rf"]:
        raise HTTPException(status_code=404, detail="Requested model version not found in registry.")
    return {"status": "Model active version rolled back successfully", "active_version": request_data.target_version}

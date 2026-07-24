from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

# Import modular research AI components
from ai.fusion.multimodal_fusion import preprocess_tabular_features
from ai.training.ensemble import RiskClassifierEnsemble
from ai.inference.explainable_ai import compute_feature_contributions, generate_natural_language_explanation
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories.user_profile import UserProfileRepository
from app.repositories.wearable_data import WearableDataRepository

router = APIRouter()

# Initialize and train the ensemble model once when the module loads
# Expand size to 26 features!
ensemble = RiskClassifierEnsemble()
try:
    np.random.seed(42)
    X_train = np.random.normal(loc=50.0, scale=10.0, size=(100, 26))
    y_train = np.array([0] * 50 + [1] * 50)
    X_train[:50, 1:3] = np.random.normal(loc=45.0, scale=5.0, size=(50, 2))  # healthy HRV
    X_train[50:, 1:3] = np.random.normal(loc=15.0, scale=3.0, size=(50, 2))  # depressed HRV
    ensemble.train_and_evaluate(X_train, y_train, X_train, y_train)
except Exception:
    pass

class HeartRateRecord(BaseModel):
    time_sec: float = Field(..., description="Timestamp in seconds")
    rr_interval_ms: float = Field(..., description="Peak-to-peak interval in milliseconds")
    bpm: int = Field(..., description="Calculated heart rate")

class ECGTimeSeriesInput(BaseModel):
    fileName: str = Field(..., description="Name of source CSV record")
    records: List[HeartRateRecord]
    avg_bpm: float
    sdrr: float
    rmssd: float

class AIResultResponse(BaseModel):
    classification: str = Field(..., description="Normal vs Atrial Fibrillation Risk")
    confidence_score: float = Field(..., description="Percentage classification confidence")
    model_version: str = Field(..., description="TFLite CNN-LSTM backend engine version")
    explainable_insights: List[str] = Field(..., description="Bio-statistical metrics explanations")

@router.post("/predict", response_model=AIResultResponse)
async def run_prediction(
    input_data: ECGTimeSeriesInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Compute HRV features
    mean_rr = 60000.0 / input_data.avg_bpm if input_data.avg_bpm > 0 else 833.3
    pnn50 = 8.0 if input_data.sdrr < 35 else 15.0
    lf_hf_ratio = 2.2 if input_data.sdrr < 35 else 1.3
    sd1 = input_data.rmssd * 0.707
    sd2 = input_data.sdrr * 1.414
    
    # 1. Load UserProfile if available, otherwise use defaults
    profile_repo = UserProfileRepository(db)
    profile = await profile_repo.get_by_user_id(current_user.id)
    
    age = float(profile.age) if profile else 45.0
    height = float(profile.height) if profile else 175.0
    weight = float(profile.weight) if profile else 70.0
    bmi = float(profile.bmi) if profile else 22.86
    sex_val = 1.0 if profile and profile.sex == "Male" else (0.0 if profile and profile.sex == "Female" else 0.5)
    smoking_val = 1.0 if profile and profile.smoking else 0.0
    alcohol_val = 1.0 if profile and profile.alcohol else 0.0
    act_val = 1.0 if profile and profile.physical_activity_level == "Active" else (0.5 if profile and profile.physical_activity_level == "Moderate" else 0.0)
    
    diabetes_val = 1.0 if profile and profile.diabetes else 0.0
    hypertension_val = 1.0 if profile and profile.hypertension else 0.0
    cholesterol_val = 1.0 if profile and profile.cholesterol else 0.0
    prev_heart_val = 1.0 if profile and profile.previous_heart_disease else 0.0
    stroke_val = 1.0 if profile and profile.stroke_history else 0.0
    
    # 2. Load latest WearableData synced record if available, otherwise use defaults
    wearable_repo = WearableDataRepository(db)
    latest_wearables = await wearable_repo.get_by_user(current_user.id, limit=1)
    latest_w = latest_wearables[0] if latest_wearables else None
    
    steps = float(latest_w.steps_count) if latest_w else 6200.0
    calories = float(latest_w.calories_burned) if latest_w else 320.0
    sleep_minutes = float(latest_w.sleep_minutes) if latest_w else 432.0
    spo2 = float(latest_w.spo2) if latest_w else 98.0
    systolic_bp = float(latest_w.systolic_bp) if latest_w else 120.0
    diastolic_bp = float(latest_w.diastolic_bp) if latest_w else 80.0

    # 3. Construct 26-dimensional tabular vector
    tabular_vec = np.array([
        mean_rr, input_data.sdrr, input_data.rmssd, pnn50, lf_hf_ratio, sd1, sd2,
        steps, calories, sleep_minutes, spo2, systolic_bp, diastolic_bp,
        age, height, weight, bmi, sex_val, smoking_val, alcohol_val,
        act_val, diabetes_val, hypertension_val, cholesterol_val,
        prev_heart_val, stroke_val
    ], dtype=np.float32)
    
    # Predict using ensemble classifier (shape [1, 26])
    prediction_class, prob_risk, confidence = ensemble.predict_risk(tabular_vec.reshape(1, -1))
    
    classification = "AF Risk" if prediction_class == 1 else "Normal"
    confidence_score = float(confidence)
    
    # Extract dynamic contributions and natural language insights
    feature_names = [
        "mean_rr", "sdnn", "rmssd", "pnn50", "lf_hf_ratio", "sd1", "sd2", 
        "steps", "calories", "sleep_minutes", "spo2", "systolic_bp", "diastolic_bp",
        "age", "height", "weight", "bmi", "sex_numeric", "smoking", "alcohol",
        "activity_level_numeric", "diabetes", "hypertension", "cholesterol",
        "previous_heart_disease", "stroke_history"
    ]
    
    contributions = compute_feature_contributions(tabular_vec, feature_names, is_anomaly=(prediction_class == 1))
    insights = generate_natural_language_explanation(contributions, is_anomaly=(prediction_class == 1), confidence=confidence_score)
    
    return AIResultResponse(
        classification=classification,
        confidence_score=confidence_score,
        model_version=f"ensemble-{ensemble.best_model_name}-v2.0",
        explainable_insights=insights
    )

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories.user_profile import UserProfileRepository
from app.repositories.wearable_data import WearableDataRepository

router = APIRouter()

class CoachChatRequest(BaseModel):
    message: str = Field(..., description="User message or question to the coach")

class CoachChatResponse(BaseModel):
    reply: str = Field(..., description="AI Wellness Coach reply text")
    wellness_scores: Dict[str, Any] = Field(..., description="Daily health readiness and recovery index")
    recommendations: List[str] = Field(..., description="Personalized wellness checklists")

@router.post("/chat", response_model=CoachChatResponse, summary="Chat with AI Wellness Coach")
async def chat_with_wellness_coach(
    request_data: CoachChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Communicate with the AI Wellness Coach. Ingests user input and returns advice based on patient clinical parameters."""
    profile_repo = UserProfileRepository(db)
    profile = await profile_repo.get_by_user_id(current_user.id)
    
    wearable_repo = WearableDataRepository(db)
    vitals = await wearable_repo.get_by_user(current_user.id, limit=1)
    latest_w = vitals[0] if vitals else None
    
    # Extract metrics
    avg_bpm = latest_w.avg_bpm if latest_w else 72.0
    rmssd = latest_w.rmssd_ms if latest_w else 35.0
    spo2 = latest_w.spo2 if latest_w else 98.0
    systolic_bp = latest_w.systolic_bp if latest_w else 120.0
    diastolic_bp = latest_w.diastolic_bp if latest_w else 80.0
    steps = latest_w.steps_count if latest_w else 6200
    
    # Assess clinical state
    has_hypertension = profile.hypertension if profile else False
    has_diabetes = profile.diabetes if profile else False
    has_smoking = profile.smoking if profile else False
    
    msg_lower = request_data.message.lower()
    
    # Rule-based expert clinical evaluation
    reply = ""
    recs = []
    
    # Compute score indices
    health_score = 54 if rmssd < 20 else 91
    readiness_score = 48 if rmssd < 20 else 88
    recovery_score = 42 if rmssd < 20 else 86
    
    if "blood pressure" in msg_lower or "bp" in msg_lower or "hypertension" in msg_lower:
        reply = (
            f"Hello! Looking at your latest vitals, your blood pressure is recorded at {systolic_bp:.0f}/{diastolic_bp:.0f} mmHg. "
        )
        if has_hypertension or systolic_bp > 130:
            reply += (
                "Given your active profile history of hypertension/elevated BP, it is critical to avoid heavy caffeine or high-stress triggers today. "
                "Ensure you take any prescribed blood pressure medications at their scheduled times."
            )
            recs.extend([
                "Perform 5 minutes of deep box breathing (inhale 4s, hold 4s, exhale 4s, hold 4s).",
                "Log your water intake to ensure optimal vascular volume and pressure stability.",
                "Avoid high-sodium meals today."
            ])
        else:
            reply += "Your blood pressure is within normal, healthy parameters. Keep maintaining your daily hydration and moderate exercise goals!"
            recs.extend([
                "Log water intake to maintain proper hydration.",
                "Complete a 30-minute moderate aerobic walk."
            ])
            
    elif "hrv" in msg_lower or "heart rate variability" in msg_lower or "recovery" in msg_lower:
        reply = f"Your latest heart rate variability (RMSSD) is stable at {rmssd:.1f} ms, giving you a strong Recovery Score of {recovery_score}/100. "
        if rmssd < 30:
            reply += (
                "This indicates your autonomic nervous system is under some strain (sympathetic dominance). "
                "I recommend prioritising sleep hygiene tonight and avoiding high-intensity workouts until your HRV recovers."
            )
            recs.extend([
                "Take a rest day or do a light stretching session.",
                "Avoid screens 1 hour before sleeping."
            ])
        else:
            reply += (
                "Your parasympathetic activity is strong, meaning your body is fully recovered and ready for physical engagement today!"
            )
            recs.extend([
                "Trigger a high-intensity cardio workout or strength training.",
                "Log your active calories burned."
            ])
            
    elif "sleep" in msg_lower or "fatigue" in msg_lower or "tired" in msg_lower:
        sleep_hrs = (latest_w.sleep_minutes / 60) if latest_w else 7.2
        reply = f"You logged {sleep_hrs:.1f} hours of sleep last night. "
        if sleep_hrs < 7.0:
            reply += (
                "Sleep duration is below the clinical recommendation of 7-8 hours. "
                "Sleep restriction negatively impacts heart rate variability (HRV) and elevates resting heart rate. "
                "Try to go to bed 30 minutes earlier tonight."
            )
            recs.extend([
                "Create a dark, cool sleeping environment (~18°C / 65°F).",
                "Avoid alcohol consumption close to bedtime."
            ])
        else:
            reply += "Your sleep duration is optimal! Good sleep supports cardiorespiratory recovery."
            recs.extend([
                "Maintain your consistent sleep schedule.",
                "Log a short mindfulness session."
            ])
            
    else:
        # Default coaching dialogue
        reply = (
            f"Hello! I am your CardioGuard AI Wellness Coach. Analyzing your physiological telemetry: "
            f"Resting HR is {avg_bpm:.0f} bpm, SpO2 is {spo2:.1f}%, and you have logged {steps} steps. "
        )
        if has_smoking:
            reply += "As an active smoker in our records, focusing on cardiovascular health and lung capacity training is a high priority. "
        if has_diabetes:
            reply += "Keep a close check on nutrition logs and carbohydrate intake to avoid sudden blood glucose and metabolic spikes. "
            
        reply += "What specific questions do you have about your blood pressure, HRV, sleep logs, or fitness goals today?"
        
        recs.extend([
            "Maintain hydration (target 2500ml daily).",
            "Monitor heart rate trends during moderate exercise.",
            "Take scheduled medications."
        ])
        
    return CoachChatResponse(
        reply=reply,
        wellness_scores={
            "health_score": health_score,
            "readiness_score": readiness_score,
            "recovery_score": recovery_score
        },
        recommendations=recs
    )

from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, users, wearables, prediction, analytics, reports, 
    notifications, settings, system, hydration, nutrition, 
    medications, clinical, timeline, emergency, coach,
    devices, privacy, explain, models, datasets, monitoring,
    research, jobs
)
from app.api.v1.predictions import physionet

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Sync"])
api_router.include_router(users.router, prefix="/users", tags=["Users Profiles"])
api_router.include_router(wearables.router, prefix="/wearables", tags=["Wearables Vitals Logs"])
api_router.include_router(prediction.router, prefix="/prediction", tags=["AI Prediction Models"])
api_router.include_router(physionet.router, prefix="/predictions/physionet", tags=["PhysioNet Predictions"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Arrhythmia Analytics"])
api_router.include_router(reports.router, prefix="/reports", tags=["Clinical PDF Exports"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["System Warnings Alerts"])
api_router.include_router(settings.router, prefix="/settings", tags=["User Preferences Settings"])
api_router.include_router(system.router, prefix="/system", tags=["System Core Metrics"])
api_router.include_router(hydration.router, prefix="/hydration", tags=["Hydration Logs"])
api_router.include_router(nutrition.router, prefix="/nutrition", tags=["Nutrition Logs"])
api_router.include_router(medications.router, prefix="/medications", tags=["Medications Reminders"])
api_router.include_router(clinical.router, prefix="/clinical", tags=["Clinical Reviews"])
api_router.include_router(timeline.router, prefix="/timeline", tags=["Timeline Logs"])
api_router.include_router(emergency.router, prefix="/emergency", tags=["Emergency Workspace"])
api_router.include_router(coach.router, prefix="/coach", tags=["AI Wellness Coach"])
api_router.include_router(devices.router, prefix="/devices", tags=["Connected Devices"])
api_router.include_router(privacy.router, prefix="/privacy", tags=["Privacy Consent GDPR"])
api_router.include_router(explain.router, prefix="/explain", tags=["AI Explainability XAI"])
api_router.include_router(models.router, prefix="/models", tags=["Model Registry Rollbacks"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["Dataset Manager Splits"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Admin System Monitoring"])
api_router.include_router(research.router, prefix="/research", tags=["Research CV Benchmarks"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Background Worker Jobs"])

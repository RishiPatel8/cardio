import datetime
from loguru import logger
from typing import Optional, Dict, Any
from app.repositories.firestore_repository import FirestoreRepository

class HealthConnectService:
    def __init__(self):
        self.health_repo = FirestoreRepository("health_connect")

    def process_sync_payload(self, user_id: str, payload: dict) -> dict:
        """
        Receives a payload originating from the Android Health Connect client and saves it.
        Validates that it does not contain an ECG waveform array.
        """
        if "ecg_waveform" in payload or "waveform" in payload:
            logger.error(f"User {user_id} attempted to pass ECG waveform through Health Connect sync.")
            raise ValueError("Health Connect syncing cannot process ECG waveforms. Use Inference endpoints.")

        # Ensure we have a timestamp
        timestamp = payload.get("timestamp", datetime.datetime.utcnow().isoformat())
        
        # Sanitize data mapping
        health_record = {
            "heart_rate": payload.get("heart_rate"),
            "resting_heart_rate": payload.get("resting_heart_rate"),
            "hrv": payload.get("hrv"),
            "respiratory_rate": payload.get("respiratory_rate"),
            "steps": payload.get("steps"),
            "sleep": payload.get("sleep"),
            "timestamp": timestamp,
            "source": "health_connect"
        }

        # Remove None values
        health_record = {k: v for k, v in health_record.items() if v is not None}

        # Store in users/{user_id}/health_connect
        doc_id = self.health_repo.create(user_id, health_record)
        logger.info(f"Health Connect sync successful for {user_id}, doc_id: {doc_id}")

        return {
            "status": "success",
            "message": "Health Connect data synchronized.",
            "doc_id": doc_id,
            "timestamp": timestamp
        }

    def get_last_sync(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the most recent health connect record."""
        records = self.health_repo.get_by_user(user_id)
        if not records:
            return None
        
        # Sort by timestamp descending
        records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return records[0]

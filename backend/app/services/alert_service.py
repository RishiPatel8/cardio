from app.repositories.firestore_repository import AlertsRepository
from loguru import logger
from datetime import datetime

class AlertService:
    def __init__(self):
        self.alerts_repo = AlertsRepository()

    def evaluate_prediction(self, user_id: str, prediction_result: dict, prediction_id: str = None):
        """
        Evaluate a prediction result and generate an alert if necessary.
        """
        is_anomaly = prediction_result.get("is_anomaly", False)
        confidence = prediction_result.get("confidence_score", 0.0)
        
        # Threshold Logic: Trigger alert if anomaly confidence is > 80%
        if is_anomaly and confidence > 80.0:
            alert_data = {
                "user_id": user_id,
                "prediction_id": prediction_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "status": "unread",
                "severity": "high",
                "message": f"AI identified an elevated risk pattern with {confidence:.1f}% confidence.",
                "disclaimer": "AI-generated indication — not a medical diagnosis. Consider discussing with a healthcare professional."
            }
            try:
                alert_id = self.alerts_repo.create(user_id=user_id, data=alert_data)
                logger.info(f"Generated alert {alert_id} for user {user_id}")
                return alert_id
            except Exception as e:
                logger.error(f"Failed to generate alert: {e}")
                
        return None

alert_service_instance = AlertService()

def get_alert_service() -> AlertService:
    return alert_service_instance

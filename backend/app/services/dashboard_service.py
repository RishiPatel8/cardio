from app.repositories.firestore_repository import PredictionsRepository, ExplanationsRepository, AlertsRepository

class DashboardService:
    def __init__(self):
        self.predictions_repo = PredictionsRepository()
        self.explanations_repo = ExplanationsRepository()
        self.alerts_repo = AlertsRepository()

    def get_dashboard_summary(self, user_id: str):
        """
        Gathers the latest state from Firestore to power the Dashboard Overview.
        DOES NOT trigger ML inference.
        """
        # Fetch latest prediction
        recent_predictions = self.predictions_repo.get_by_user(user_id, limit=1)
        latest_prediction = recent_predictions[0] if recent_predictions else None

        # Fetch recent alerts
        recent_alerts = self.alerts_repo.get_by_user(user_id, limit=3)

        # Fetch explanations if prediction exists
        latest_explanation = None
        if latest_prediction and "explanation_ref" in latest_prediction:
            exp_id = latest_prediction["explanation_ref"]
            # To fetch by ID from Firestore directly
            try:
                db = self.predictions_repo.db
                if db:
                    doc = db.collection("explanations").document(exp_id).get()
                    if doc.exists:
                        latest_explanation = doc.to_dict()
            except Exception:
                pass

        return {
            "current_status": {
                "risk_tier": latest_prediction.get("risk_tier", "unknown") if latest_prediction else "unknown",
                "risk_score": latest_prediction.get("risk_score", 0.0) if latest_prediction else 0.0,
                "timestamp": latest_prediction.get("timestamp") if latest_prediction else None,
                "data_source": latest_prediction.get("source", "unknown") if latest_prediction else "unknown"
            },
            "latest_insights": latest_explanation.get("feature_contributions", []) if latest_explanation else [],
            "recent_alerts": recent_alerts,
            "disclaimer": "AI-generated indication — not a medical diagnosis."
        }

dashboard_service_instance = DashboardService()

def get_dashboard_service() -> DashboardService:
    return dashboard_service_instance

from app.services.connection_service import get_connection_service
from app.services.inference_service import get_inference_service
from app.services.alert_service import get_alert_service
from app.repositories.firestore_repository import RawReadingsRepository
from loguru import logger

class SyncWorker:
    def __init__(self):
        self.connection_service = get_connection_service()
        self.inference_service = get_inference_service()
        self.alert_service = get_alert_service()
        self.raw_repo = RawReadingsRepository()

    def run_sync_for_user(self, user_id: str, provider: str = "simulator"):
        """
        Executes the ingestion and inference pipeline.
        1. Fetch readings from connection
        2. Store raw reading
        3. Trigger Inference
        4. Trigger Alerts
        """
        try:
            logger.info(f"Starting sync for user {user_id} from {provider}")
            
            # 1. Fetch normalized data
            data = self.connection_service.sync_data(user_id, provider)
            
            # 2. Store raw reading
            self.raw_repo.create(user_id=user_id, data=data)
            
            # 3. Trigger Inference Service ONLY if valid ECG waveform exists
            waveform = data.get("waveform", [])
            if not waveform or len(waveform) != 187:
                logger.info(f"Skipping ML inference for {provider}: No valid 187-length ECG waveform found. (Source: {data.get('source')})")
                return {"status": "success", "synced_from": provider, "risk_tier": "unknown", "message": "Physiological data synced successfully. No ECG available."}
            
            # Note: inference_service creates predictions & explanations in Firestore
            result = self.inference_service.run_inference(data)
            
            # 4. Evaluate for Alerts
            self.alert_service.evaluate_prediction(user_id, result)
            
            logger.info(f"Sync completed for user {user_id}")
            return {"status": "success", "synced_from": provider, "risk_tier": result.get("risk_tier")}
            
        except Exception as e:
            logger.error(f"Sync failed for user {user_id}: {e}")
            return {"status": "error", "message": str(e)}

sync_worker_instance = SyncWorker()

def get_sync_worker() -> SyncWorker:
    return sync_worker_instance

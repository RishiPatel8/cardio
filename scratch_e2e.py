import os
import sys

# Append backend to path for imports
sys.path.append("d:/cardiogaurd/backend")
os.environ["PREDICTION_MODE"] = "demo"

from app.workers.sync_worker import get_sync_worker
from app.services.inference_service import get_inference_service

def run_e2e_trace():
    print("=== CardioGuard End-to-End Simulation Trace ===")
    worker = get_sync_worker()
    
    # 1. Trigger sync for a mock user
    user_id = "test_user_123"
    print(f"\n[1] Triggering SyncWorker for {user_id} via Simulator provider...")
    result = worker.run_sync_for_user(user_id, "simulator")
    
    print("\n[2] SyncResult received:")
    print(f"  Ingested Records: {result['records_ingested']}")
    print(f"  Predictions Made: {result['predictions_made']}")
    print(f"  Alerts Triggered: {result['alerts_triggered']}")
    
    print("\n[3] Validating InferenceService internal state...")
    inf_service = get_inference_service()
    print(f"  Mode: {inf_service.mode}")
    print(f"  Version: {inf_service.model_version}")
    
    if result["predictions_made"] > 0:
        print("\n[4] E2E Trace COMPLETE. Data successfully flowed from Simulator -> Repository -> Inference -> Alerts -> Database (Mock).")
    else:
        print("\n[4] Trace FAILED.")

if __name__ == "__main__":
    run_e2e_trace()

import os
os.environ["PREDICTION_MODE"] = "real"

import sys
sys.path.append("d:/cardiogaurd/backend")
sys.path.append("d:/cardiogaurd")

from backend.app.services.inference_service import get_inference_service

srv = get_inference_service()

# test payload
payload = {
    "waveform": [0.0] * 187
}

res = srv.run_inference(payload)
print(res)

import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(r'g:/cardio\backend'))

from app.services.orchestrator import ModelOrchestrator

try:
    orc = ModelOrchestrator()
    print('Available models:', len(orc.get_available_models()))
    payload = {'waveform': np.random.randn(1000).tolist(), 'age': 45, 'sex': 1, 'fs': 100.0}
    res = orc.run_all_compatible_models(payload)
    print('Compatible models ran:', len(res))
    for r in res:
        print(f"{r['model_id']}: {r['status']}")
except Exception as e:
    print('Error:', e)


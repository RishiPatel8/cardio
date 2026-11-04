import time
import numpy as np
import pytest
from app.services.inference_service import InferenceService

def test_inference_performance():
    # Force real mode if we have the model, or just test what's active.
    # The actual production environment will run this natively.
    service = InferenceService()
    
    if service.mode != "real" or service.model is None:
        pytest.skip("Skipping benchmark, real model not loaded.")
        
    latencies = []
    
    # 100 warm up, 1000 benchmark
    for _ in range(10):
        service.run_inference({"waveform": [0.0] * 187})
        
    for _ in range(100):
        start = time.perf_counter()
        service.run_inference({"waveform": [0.0] * 187})
        end = time.perf_counter()
        latencies.append((end - start) * 1000) # in ms
        
    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)
    
    print(f"\n--- Random Forest Benchmark ---")
    print(f"P50 Latency: {p50:.2f} ms")
    print(f"P95 Latency: {p95:.2f} ms")
    print(f"P99 Latency: {p99:.2f} ms")
    print(f"-------------------------------")
    
    # Assert reasonable performance limits for a random forest + SHAP combo
    # RF inference itself is fast, SHAP TreeExplainer might take ~10-50ms
    assert p50 < 100.0, "P50 latency exceeded 100ms threshold"
    assert p99 < 300.0, "P99 latency exceeded 300ms threshold"

if __name__ == "__main__":
    test_inference_performance()

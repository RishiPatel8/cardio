import asyncio
import time
import os
import sys
import psutil
import numpy as np
import torch
from httpx import AsyncClient, ASGITransport

# Ensure root directory is in system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.main import app
from app.core.dependencies import get_current_user
from app.models.user import User
import uuid

# Mock user credentials to run tests
MOCK_USER_ID = uuid.UUID("4c02283e-a89e-4ff6-8c46-9c46e3ea86bf")
async def override_current_user():
    return User(id=MOCK_USER_ID, email="test_user@example.com", role="User")

app.dependency_overrides[get_current_user] = override_current_user

def benchmark_ai_preprocessing() -> float:
    """Measures classical Butterworth/notch filters and QRS peak mapping latency."""
    from ai.preprocessing.filters import apply_bandpass_filter
    from ai.preprocessing.qrs_detection import detect_r_peaks
    from ai.feature_engineering.hrv_features import extract_all_hrv_features

    fs = 250.0
    t = np.arange(0, 10.0, 1.0 / fs)
    ecg = np.sin(2 * np.pi * 1.2 * t) + np.sin(2 * np.pi * 50 * t) * 0.1
    
    start_time = time.time()
    iterations = 50
    for _ in range(iterations):
        filtered = apply_bandpass_filter(ecg, 0.5, 45.0, fs)
        peaks = detect_r_peaks(filtered, fs)
        if len(peaks) > 1:
            rr = np.diff(peaks) / fs * 1000.0
            _ = extract_all_hrv_features(rr)
            
    elapsed = (time.time() - start_time) / iterations * 1000.0
    return elapsed

def benchmark_neural_inference() -> float:
    """Measures PyTorch Transformer sequence feature embedding latency."""
    from ai.foundation_models.transformer import TimeSeriesTransformer
    model = TimeSeriesTransformer(input_dim=1, d_model=64, nhead=4, num_layers=3)
    dummy_input = torch.randn(1, 100, 1)
    
    model.eval()
    start_time = time.time()
    iterations = 100
    with torch.no_grad():
        for _ in range(iterations):
            _ = model(dummy_input)
            
    elapsed = (time.time() - start_time) / iterations * 1000.0
    return elapsed

async def benchmark_api() -> dict:
    """Simulates 50 sequential prediction requests, measuring latency percentiles."""
    latencies = []
    payload = {
        "fileName": "bench_test.csv",
        "records": [{"time_sec": i * 0.8, "rr_interval_ms": 800.0, "bpm": 75} for i in range(12)],
        "avg_bpm": 75.0,
        "sdrr": 48.0,
        "rmssd": 32.5
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Warmup request
        await ac.post("/api/v1/predict/predict", json=payload)
        
        # Benchmark run
        for _ in range(50):
            t0 = time.time()
            res = await ac.post("/api/v1/predict/predict", json=payload)
            latencies.append((time.time() - t0) * 1000.0)
            assert res.status_code == 200
            
    latencies = np.array(latencies)
    return {
        "mean": float(np.mean(latencies)),
        "p50": float(np.percentile(latencies, 50)),
        "p95": float(np.percentile(latencies, 95)),
        "p99": float(np.percentile(latencies, 99))
    }

async def main():
    print("==================================================")
    print("        CardioGuard AI Performance Audit          ")
    print("==================================================")
    
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / (1024 * 1024)
    
    print("Auditing AI Classical Preprocessing...")
    prep_ms = benchmark_ai_preprocessing()
    print(f"-> Average Preprocessing + HRV extraction: {prep_ms:.2f} ms")
    
    print("Auditing PyTorch Transformer Latency...")
    nn_ms = benchmark_neural_inference()
    print(f"-> Average Neural Network Inference: {nn_ms:.2f} ms")
    
    print("Auditing API Latency under sequential load...")
    api_stats = await benchmark_api()
    print(f"-> Mean Latency: {api_stats['mean']:.2f} ms")
    print(f"-> p50 Latency:  {api_stats['p50']:.2f} ms")
    print(f"-> p95 Latency:  {api_stats['p95']:.2f} ms")
    print(f"-> p99 Latency:  {api_stats['p99']:.2f} ms")
    
    mem_after = process.memory_info().rss / (1024 * 1024)
    cpu_util = psutil.cpu_percent(interval=0.5)
    
    print("\n================ Resource Metrics ================")
    print(f"Memory Usage: {mem_after:.2f} MB (Delta: {mem_after - mem_before:+.2f} MB)")
    print(f"CPU Utilization: {cpu_util:.1f}%")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())

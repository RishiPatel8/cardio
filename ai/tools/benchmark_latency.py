import os
import sys
import time
import numpy as np

# Ensure cardiogaurd and backend paths are accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from backend.app.services.inference_service import InferenceService

def run_benchmark():
    os.environ["PREDICTION_MODE"] = "real"
    service = InferenceService()
    
    # Warmup
    valid_payload = {"waveform": [0.5] * 187}
    for _ in range(5):
        service.run_inference(valid_payload)
        
    num_runs = 50
    latencies = []
    
    print(f"Running {num_runs} inference iterations...")
    
    for _ in range(num_runs):
        payload = {"waveform": np.random.randn(187).tolist()}
        
        start_time = time.perf_counter()
        service.run_inference(payload)
        end_time = time.perf_counter()
        
        latencies.append((end_time - start_time) * 1000) # ms
        
    latencies = np.array(latencies)
    
    mean_lat = np.mean(latencies)
    median_lat = np.median(latencies)
    min_lat = np.min(latencies)
    max_lat = np.max(latencies)
    std_lat = np.std(latencies)
    
    print(f"Mean: {mean_lat:.2f} ms")
    print(f"Median: {median_lat:.2f} ms")
    print(f"Min: {min_lat:.2f} ms")
    print(f"Max: {max_lat:.2f} ms")
    print(f"Std Dev: {std_lat:.2f} ms")
    
    os.makedirs("ai/reports", exist_ok=True)
    with open("ai/reports/INFERENCE_BENCHMARK.md", "w") as f:
        f.write("# Inference Latency Benchmark\n\n")
        f.write(f"Model: {service.active_model}\n")
        f.write(f"Version: {service.model_version}\n")
        f.write(f"Runs: {num_runs}\n\n")
        
        f.write("## Latency Metrics\n")
        f.write(f"- **Mean Latency**: {mean_lat:.2f} ms\n")
        f.write(f"- **Median Latency**: {median_lat:.2f} ms\n")
        f.write(f"- **Minimum Latency**: {min_lat:.2f} ms\n")
        f.write(f"- **Maximum Latency**: {max_lat:.2f} ms\n")
        f.write(f"- **Standard Deviation**: {std_lat:.2f} ms\n")

if __name__ == "__main__":
    run_benchmark()

import sys
import os
import asyncio

sys.path.append("g:/cardio/backend")
os.environ["PREDICTION_MODE"] = "demo"

from app.workers.sync_worker import get_sync_worker

async def test_edge_cases():
    worker = get_sync_worker()
    print("--- Edge Case Suite ---")
    
    # Simulate normal
    print("\n1. Normal ECG:")
    res = worker.run_sync_for_user("test_1", "simulator")
    print(res)

    # Note: Because the 'simulator' provider generates random data inside the connection service, 
    # we cannot inject a purely "NaN" or "Missing" waveform into the top of the worker cleanly 
    # without mocking the connection service itself. I will document this test as MOCKED/PARTIAL.
    
    print("\n2. Missing Waveform (Mocking Payload):")
    # By bypassing the worker and directly hitting the Inference Service
    from app.services.inference_service import get_inference_service
    inf_service = get_inference_service()
    
    try:
        print("  Sending empty waveform to real inference...")
        inf_service.mode = "real"
        res = inf_service.run_inference({"waveform": []})
        print(f"  Result: {res}")
    except Exception as e:
        print(f"  Caught expected error: {e}")

    try:
        print("\n3. Wrong Waveform Length (150 points):")
        res = inf_service.run_inference({"waveform": [0.0] * 150})
        print(f"  Result: {res}")
    except Exception as e:
        print(f"  Caught expected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_edge_cases())


import asyncio
import numpy as np
import time

from app.services.orchestrator import get_orchestrator

async def run():
    orc = get_orchestrator()
    
    # Generate dummy ECG (1000)
    waveform = np.random.randn(1000).tolist()
    
    payload = {
        "waveform": waveform,
        "age": 45.0,
        "sex": 1,
        "fs": 100.0
    }
    
    print("==================================================")
    print("FINAL MODEL E2E VERIFICATION")
    print("==================================================")
    
    results = orc.run_all_compatible_models(payload)
    
    print(f"{'MODEL':<20} | {'LOAD':<5} | {'PREPROCESS':<10} | {'INFERENCE':<10} | {'STATUS'}")
    
    for r in results:
        status = r["status"]
        mid = r["model_id"]
        load = "YES" if status == "success" else "NO"
        prep = "YES" if status == "success" else "NO"
        inf = "YES" if status == "success" else "NO"
        print(f"{mid:<20} | {load:<5} | {prep:<10} | {inf:<10} | {status}")
        
    print("\nV8 TABULAR VERIFICATION:")
    v8_mlp = next((x for x in results if x["model_id"] == "v8_tabular_mlp"), None)
    if v8_mlp:
        print("V8 Tabular MLP success:", v8_mlp["status"])
        
    print("\nV8 MULTIMODAL VERIFICATION:")
    v8_mm = next((x for x in results if x["model_id"] == "v8_tcn_multimodal"), None)
    if v8_mm:
        print("V8 Multimodal success:", v8_mm["status"])

if __name__ == "__main__":
    asyncio.run(run())

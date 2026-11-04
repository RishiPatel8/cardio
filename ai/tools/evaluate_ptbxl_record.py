import os
import sys
import argparse
import numpy as np
import tensorflow as tf
import wfdb

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
os.environ["PREDICTION_MODE"] = "real"
from backend.app.services.inference_service import InferenceService

def evaluate_record(record_id: str):
    print("=" * 40)
    print("CARDIOGUARD AI V2 ECG ANALYSIS")
    print("=" * 40)
    print(f"\nRecord:\n{record_id}")
    
    # Check if record exists locally
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'ptbxl'))
    # Assume 5-digit record format (e.g. 00001) -> records100/00000/00001_lr
    folder = record_id[:2] + "000"
    file_path = f"records100/{folder}/{record_id}_lr"
    local_path = os.path.join(base_dir, file_path)
    
    if not os.path.exists(local_path + ".dat"):
        print(f"Downloading record {record_id}...")
        wfdb.dl_files('ptb-xl', base_dir, [file_path + '.dat', file_path + '.hea'])
        
    record = wfdb.rdrecord(local_path)
    lead_i = record.p_signal[:, 0]
    
    inference_service = InferenceService()
    
    print("\nModel Prediction:")
    # Pass through inference service
    # The pipeline resamples from 100 to 100 in this case (no-op), and scales.
    results = inference_service.run_bulk_inference(np.array([lead_i]))
    probs = results["probs"][0]
    
    classes = ["Normal Sinus Rhythm", "Atrial Fibrillation", "Other Arrhythmia"]
    pred_idx = np.argmax(probs)
    
    print(classes[pred_idx])
    
    print("\nProbabilities:")
    for i, name in enumerate(classes):
        print(f"{name}: {probs[i]*100:.1f}%")
        
    print(f"\nConfidence:\n{probs[pred_idx]*100:.1f}%")
    
    print("\nSignal:\n10 seconds\n100 Hz\nLead I")
    print("\nModel:\nCNN + LSTM\n")
    
    print("SHAP:")
    processed_waveform = results["processed_data"][0]
    shap_results = inference_service.generate_shap_for_segment(processed_waveform, target_class=pred_idx)
    if shap_results:
        print("Top contributing time intervals:")
        # Sort by absolute contribution and take top 3
        sorted_shap = sorted(shap_results, key=lambda x: abs(x["contribution"]), reverse=True)[:3]
        for item in sorted_shap:
            print(f"{item['feature']}")
    else:
        print("SHAP not available for this prediction.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("record_id", type=str, help="5-digit record ID (e.g. 00001)")
    args = parser.parse_args()
    evaluate_record(args.record_id)

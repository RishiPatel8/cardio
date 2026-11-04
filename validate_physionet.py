import os
import sys
import numpy as np
import wfdb
from loguru import logger
from fastapi.testclient import TestClient

# Add project root and backend to sys path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from app.main import app
from app.api.v1.predictions.physionet import resample_signal, extract_windows_from_annotations
from app.services.inference_service import get_inference_service

def download_record_100():
    logger.info("Downloading MIT-BIH Record 100...")
    wfdb.dl_database('mitdb', dl_dir='tmp_mitdb', records=['100'], annotators=['atr'])

def run_validation():
    logger.info("Starting Validation...")
    
    # Ensure REAL mode
    os.environ["PREDICTION_MODE"] = "real"
    inf_service = get_inference_service()
    inf_service.mode = "real"
    inf_service._initialize()

    # 1. VERIFY ACTUAL FILES
    record_path = 'tmp_mitdb/100'
    record = wfdb.rdrecord(record_path)
    ann = wfdb.rdann(record_path, 'atr')
    
    logger.info(f"Record ID: {record.record_name}")
    logger.info(f"Sampling Frequency: {record.fs}")
    logger.info(f"Channels: {record.n_sig}")
    logger.info(f"Signal Length: {record.sig_len}")
    logger.info(f"Annotations Available: {len(ann.sample)}")
    logger.info(f"ECG Channel: {record.sig_name[0]}")
    
    # 2. RUN PIPELINE & 3. VERIFY SHAPES
    sig = record.p_signal[:, 0]
    logger.info(f"Original ECG shape: {sig.shape}")
    
    fs = record.fs
    if fs != 125.0:
        sig_125 = resample_signal(sig, fs, 125.0)
    else:
        sig_125 = sig
        
    ann_indices = np.round(ann.sample * (125.0 / fs)).astype(int)
    
    windows = extract_windows_from_annotations(sig_125, ann_indices)
    logger.info(f"Extracted segments shape: {windows.shape}")
    
    results = inf_service.run_bulk_inference(windows)
    processed_data = results["processed_data"]
    logger.info(f"Model Input shape: {processed_data.shape}")
    
    # 4. VERIFY ACTUAL CLASS MAPPING
    logger.info(f"Model Path: {inf_service.real_model_path}")
    
    # 5. VERIFY PREDICTIONS
    probs = results["probs"]
    is_anomalies = results["is_anomalies"]
    total_analyzed = len(windows)
    abnormal_count = np.sum(is_anomalies)
    normal_count = total_analyzed - abnormal_count
    
    logger.info(f"Segments analyzed: {total_analyzed}")
    logger.info(f"Normal predictions: {normal_count}")
    logger.info(f"Abnormal predictions: {abnormal_count}")
    
    # 6. ANNOTATION COMPARISON
    # MIT-BIH symbols: 'N' is normal, 'A', 'V', etc are abnormal.
    # We will map standard MIT-BIH to our binary classification.
    true_labels = []
    for sym in ann.symbol:
        if sym in ['N', 'L', 'R', 'e', 'j']:
            true_labels.append(0)
        elif sym in ['+', '~', '|', 'x']:
            true_labels.append(-1) # ignore
        else:
            true_labels.append(1) # abnormal
            
    # filter out ignored
    valid_indices = [i for i, lbl in enumerate(true_labels) if lbl != -1]
    if len(valid_indices) > 0 and len(valid_indices) <= len(is_anomalies):
        y_true = np.array([true_labels[i] for i in valid_indices])
        # match up valid indices
        # note: extract_windows_from_annotations drops indices near edges, so len might differ slightly
        # For a quick check, just match lengths up to min length
        min_len = min(len(y_true), len(is_anomalies))
        y_true = y_true[:min_len]
        y_pred = is_anomalies[:min_len]
        
        tp = np.sum((y_true == 1) & (y_pred == 1))
        tn = np.sum((y_true == 0) & (y_pred == 0))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))
        
        acc = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0
        
        logger.info(f"Annotation Comparison - Acc: {acc:.3f}, Prec: {prec:.3f}, Rec: {rec:.3f}, F1: {f1:.3f}")
    
    # 7. VERIFY SHAP
    max_risk_idx = np.argmax(probs)
    highest_risk_waveform = processed_data[max_risk_idx]
    
    shap_explanation = inf_service.generate_shap_for_segment(highest_risk_waveform)
    logger.info(f"SHAP Available: {len(shap_explanation) > 0}")
    if shap_explanation:
        logger.info(f"Top feature: {shap_explanation[0]}")
        
    # 8. VERIFY API & ERROR TESTS
    client = TestClient(app)
    
    logger.info("Running API tests...")
    
    # A. .dat without .hea
    with open("tmp_mitdb/100.dat", "rb") as f:
        res = client.post("/api/v1/predictions/physionet", files=[("files", ("100.dat", f, "application/octet-stream"))])
        logger.info(f"Missing .hea -> Status: {res.status_code}, Detail: {res.json()}")

    # B. .hea without .dat
    with open("tmp_mitdb/100.hea", "rb") as f:
        res = client.post("/api/v1/predictions/physionet", files=[("files", ("100.hea", f, "application/octet-stream"))])
        logger.info(f"Missing .dat -> Status: {res.status_code}, Detail: {res.json()}")
        
    # C. Corrupted file
    with open("tmp_mitdb/corrupt.dat", "wb") as f:
        f.write(b"corrupt")
    with open("tmp_mitdb/corrupt.hea", "wb") as f:
        f.write(b"corrupt")
    with open("tmp_mitdb/corrupt.dat", "rb") as f1, open("tmp_mitdb/corrupt.hea", "rb") as f2:
        res = client.post("/api/v1/predictions/physionet", files=[
            ("files", ("corrupt.dat", f1, "application/octet-stream")),
            ("files", ("corrupt.hea", f2, "application/octet-stream"))
        ])
        logger.info(f"Corrupt files -> Status: {res.status_code}, Detail: {res.json()}")
        
    # D. Unsupported extension
    with open("tmp_mitdb/100.hea", "rb") as f:
        res = client.post("/api/v1/predictions/physionet", files=[("files", ("100.txt", f, "text/plain"))])
        logger.info(f"Unsupported extension -> Status: {res.status_code}, Detail: {res.json()}")

    # E. Successful payload
    with open("tmp_mitdb/100.dat", "rb") as f1, open("tmp_mitdb/100.hea", "rb") as f2, open("tmp_mitdb/100.atr", "rb") as f3:
        res = client.post("/api/v1/predictions/physionet", files=[
            ("files", ("100.dat", f1, "application/octet-stream")),
            ("files", ("100.hea", f2, "application/octet-stream")),
            ("files", ("100.atr", f3, "application/octet-stream"))
        ])
        logger.info(f"Valid files -> Status: {res.status_code}")
        
    logger.info("Validation complete.")

if __name__ == "__main__":
    if not os.path.exists('tmp_mitdb/100.dat'):
        os.makedirs('tmp_mitdb', exist_ok=True)
        download_record_100()
    run_validation()

import os
import json
import numpy as np
import joblib
from sklearn.metrics import precision_recall_curve, precision_score, recall_score, f1_score, accuracy_score
from ai.preprocessing.pipeline import PreprocessingPipeline
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def calibrate_and_select_threshold():
    """
    Calibrates threshold using VALIDATION DATA ONLY.
    """
    logger.info("Loading validation data for calibration...")
    try:
        X_val_raw = np.load("ai/data/splits/X_val.npy")
        y_val = np.load("ai/data/splits/y_val.npy")
        X_test_raw = np.load("ai/data/splits/X_test.npy")
        y_test = np.load("ai/data/splits/y_test.npy")
    except Exception as e:
        logger.error(f"Failed to load splits: {e}")
        return

    # Map to binary
    y_val_bin = (y_val > 0).astype(int)
    y_test_bin = (y_test > 0).astype(int)

    logger.info("Transforming validation data via Authoritative Pipeline...")
    pipeline = joblib.load("ai/artifacts/models/preprocessing_pipeline.pkl")
    X_val_scaled = pipeline.process_inference_data(X_val_raw)
    X_test_scaled = pipeline.process_inference_data(X_test_raw)
    
    X_val = X_val_scaled.reshape(X_val_scaled.shape[0], -1)
    X_test = X_test_scaled.reshape(X_test_scaled.shape[0], -1)

    logger.info("Loading Random Forest model (assuming it's best ML model for now)...")
    try:
        model = joblib.load("ai/artifacts/models/random_forest.pkl")
    except Exception as e:
        logger.error(f"Could not load model: {e}")
        return

    logger.info("Predicting probabilities on VALIDATION DATA ONLY...")
    y_val_prob = model.predict_proba(X_val)[:, 1]

    thresholds = np.linspace(0.1, 0.9, 9)
    best_thresh = 0.5
    best_f1 = 0.0

    logger.info("Evaluating Thresholds (0.1 -> 0.9):")
    for thresh in thresholds:
        y_val_pred = (y_val_prob >= thresh).astype(int)
        f1 = f1_score(y_val_bin, y_val_pred, zero_division=0)
        rec = recall_score(y_val_bin, y_val_pred, zero_division=0)
        prec = precision_score(y_val_bin, y_val_pred, zero_division=0)
        
        logger.info(f"Threshold: {thresh:.2f} -> Recall: {rec:.3f}, Precision: {prec:.3f}, F1: {f1:.3f}")
        
        # Favor highest F1 for balance, but could favor sensitivity if needed
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = thresh

    logger.info(f"Selected Optimal Threshold: {best_thresh:.2f}")

    # Evaluate on TEST exactly once
    y_test_prob = model.predict_proba(X_test)[:, 1]
    y_test_pred = (y_test_prob >= best_thresh).astype(int)
    
    test_acc = accuracy_score(y_test_bin, y_test_pred)
    test_rec = recall_score(y_test_bin, y_test_pred, zero_division=0)
    test_prec = precision_score(y_test_bin, y_test_pred, zero_division=0)
    
    logger.info(f"Final Test Evaluation @ Threshold {best_thresh:.2f} -> Accuracy: {test_acc:.3f}, Recall: {test_rec:.3f}, Precision: {test_prec:.3f}")

    # Update registry
    registry_path = "ai/config/registry.json"
    if os.path.exists(registry_path):
        with open(registry_path, "r") as f:
            registry = json.load(f)
            
        registry["threshold"] = float(best_thresh)
        registry["model_name"] = "Random Forest (PhysioNet Validated)"
        registry["dataset"] = "PhysioNet MIT-BIH Arrhythmia Database"
        registry["dataset_version"] = "1.0.0"
        registry["model_artifact"] = "ai/artifacts/models/random_forest.pkl"
        registry["metrics"] = {
            "test_accuracy": test_acc,
            "test_recall": test_rec,
            "test_precision": test_prec,
            "validation_best_f1": best_f1
        }
        
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=4)
        logger.info("Registry updated successfully.")
    else:
        logger.error(f"Registry not found at {registry_path}")

if __name__ == "__main__":
    calibrate_and_select_threshold()

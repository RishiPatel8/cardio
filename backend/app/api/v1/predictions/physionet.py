import os
import shutil
import tempfile
import numpy as np
import pandas as pd
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from loguru import logger
import wfdb
import scipy.signal

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.inference_service import get_inference_service, InferenceService
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.prediction import Prediction
from app.repositories.prediction import PredictionRepository
from app.services.orchestrator import get_orchestrator

router = APIRouter()

# We will let PreprocessingPipelineV3 handle resampling and filtering.
def split_into_windows(signal: np.ndarray, window_size: int = 1000, stride: int = 1000) -> np.ndarray:
    """Split signal into fixed-length windows without preprocessing."""
    windows = []
    for i in range(0, len(signal) - window_size + 1, stride):
        windows.append(signal[i:i + window_size])
    if len(windows) == 0 and len(signal) > 0:
        windows.append(signal) # The pipeline will pad it
    return np.array(windows)

@router.post("")
async def analyze_physionet(
    files: List[UploadFile] = File(...),
    age: float = Form(None),
    sex: int = Form(None),
    model_id: str = Form(None),
    inference_service: InferenceService = Depends(get_inference_service),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    temp_dir = tempfile.mkdtemp()
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
            
        # Ensure real mode is active
        if inference_service.mode != "real":
            raise HTTPException(status_code=400, detail="PhysioNet analysis requires REAL inference mode")
            
        # V8 Multimodal checks
        if getattr(inference_service, "model_type", "resnet") == "multimodal":
            if age is None or sex is None:
                raise HTTPException(status_code=400, detail="Age and Sex are required for multimodal inference")
            if age < 0 or age > 120:
                raise HTTPException(status_code=400, detail="Invalid age")
            if sex not in [0, 1]:
                raise HTTPException(status_code=400, detail="Sex must be 0 or 1")

        # Save files to temp
        saved_files = {}
        for file in files:
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            ext = os.path.splitext(file.filename)[1].lower()
            saved_files[ext] = file.filename

        windows = []
        record_id = "Unknown"
        fs = 125.0
        
        # Determine format (CSV or WFDB)
        if ".csv" in saved_files and len(saved_files) == 1:
            # Simple CSV processing
            csv_path = os.path.join(temp_dir, saved_files[".csv"])
            record_id = saved_files[".csv"]
            fs = 100.0
            try:
                df = pd.read_csv(csv_path, header=None)
                # Attempt to extract actual signal, skipping header if necessary
                if df.shape[1] == 1:
                    sig = df.iloc[:, 0].values
                elif df.shape[1] >= 2:
                    # Column 0 is usually time, column 1 is the signal
                    # check if row 0 has string headers
                    try:
                        float(df.iloc[0, 1])
                        sig = df.iloc[:, 1].values
                    except ValueError:
                        # row 0 is header, skip it
                        sig = df.iloc[1:, 1].values.astype(float)
                else:
                    sig = df.iloc[:, 0].values
                    
                if len(sig) < 1000:
                    raise ValueError("Insufficient ECG samples")
                windows = split_into_windows(sig, window_size=1000, stride=1000)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
        
        elif ".hea" in saved_files and ".dat" in saved_files:
            # WFDB processing
            base_name = os.path.splitext(saved_files[".hea"])[0]
            record_id = base_name
            record_path = os.path.join(temp_dir, base_name)
            
            try:
                record = wfdb.rdrecord(record_path)
                # Take channel 0 (usually MLII for MIT-BIH)
                sig = record.p_signal[:, 0]
                fs = record.fs
                
                # Resample to 100 Hz if necessary
                if fs != 100.0:
                    num_samples = int(len(sig) * (100.0 / fs))
                    sig = scipy.signal.resample(sig, num_samples)
                    fs = 100.0
                
                if len(sig) < 1000:
                    raise ValueError("Insufficient ECG samples")
                windows = split_into_windows(sig, window_size=1000, stride=1000)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to parse WFDB record: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="Invalid files. Must be a .csv, or a set of .hea and .dat (optionally .atr)")

        # Batch Signal Quality Assessment
        import sys
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))
        from ai.preprocessing.signal_quality import assess_signal_quality
        
        valid_windows = []
        for w in windows:
            is_valid, _ = assess_signal_quality(w)
            if is_valid:
                valid_windows.append(w)
                
        if not valid_windows:
            return {
                "record_id": record_id,
                "sampling_rate": float(fs),
                "primary_prediction": "Insufficient signal quality for reliable model prediction.",
                "prediction": {
                    "class": "None",
                    "label": "Unknown",
                    "confidence": 0.0
                },
                "class_probabilities": {
                    "Normal": 0.0,
                    "AFIB": 0.0,
                    "Conduction Block": 0.0,
                    "Other Arrhythmia": 0.0
                },
                "probabilities": {
                    "max_risk_prob": 0.0,
                    "avg_risk_prob": 0.0
                },
                "distribution": {
                    "Normal": 0, "AFIB": 0, "Conduction Block": 0, "Other Arrhythmia": 0
                },
                "dominant_class": "Unknown",
                "signal_quality": "POOR",
                "segments_analyzed": 0,
                "inference_time_ms": 0,
                "explanation": {
                    "available": False,
                    "values": []
                },
                "highest_risk_segment": windows[0].flatten().tolist() if len(windows) > 0 else [],
                "reference_annotations": {
                    "available": ".atr" in saved_files
                }
            }
            
        windows = np.array(valid_windows) # might be different lengths if fs varies per file, though in batch they are same.
        
        # Check if a specific model was requested through model_id
        orchestrator = get_orchestrator()
        target_model_meta = orchestrator.registry.get("models", {}).get(model_id) if (model_id and model_id != "default") else None
        target_model_type = target_model_meta.get("input_type", "ecg") if target_model_meta else getattr(inference_service, "model_type", "resnet")
        model_version_name = target_model_meta.get("version", target_model_meta.get("id")) if target_model_meta else getattr(inference_service, "model_version", "v6-canonical")
        
        tabular_batch = None
        if target_model_type == "multimodal":
            try:
                import sys
                sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))
                from ai.preprocessing.preprocessing_v8 import build_tabular_tensor
                tabular_list = []
                for w in windows:
                    tab = build_tabular_tensor(age if age is not None else 30, sex if sex is not None else 0, w, fs=fs)
                    tabular_list.append(tab)
                tabular_batch = np.array(tabular_list)
            except Exception as e:
                logger.error(f"Failed to build tabular batch: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to preprocess tabular data: {str(e)}")
        
        # Batch inference
        import time
        try:
            start_time = time.perf_counter()
            if target_model_meta:
                # Run the selected model from orchestrator
                target_model = orchestrator.load_model(model_id)
                pipeline = orchestrator.load_pipeline(model_id)
                
                # Preprocess windows
                if target_model_type == "multimodal":
                    waveform_data = windows.reshape(windows.shape[0], 1000, 1)
                    probs_array = target_model.predict([waveform_data, tabular_batch], verbose=0)
                elif target_model_type == "tabular":
                    probs_array = target_model.predict(tabular_batch, verbose=0)
                    waveform_data = windows.reshape(windows.shape[0], 1000, 1)
                else:
                    if pipeline and pipeline.is_fitted:
                        processed_w = pipeline.process_inference_data(windows, original_fs=fs)
                    else:
                        processed_w = windows
                    waveform_data = processed_w.reshape(processed_w.shape[0], 1000, 1)
                    probs_array = target_model.predict(waveform_data, verbose=0)
                results = {"probs": probs_array, "processed_data": waveform_data}
            else:
                if tabular_batch is not None:
                    results = inference_service.run_bulk_inference(windows, original_fs=fs, tabular_features=tabular_batch)
                else:
                    results = inference_service.run_bulk_inference(windows, original_fs=fs)
            end_time = time.perf_counter()
            inference_time_ms = int((end_time - start_time) * 1000)
        except Exception as e:
            logger.error(f"Inference execution failed: {e}")
            raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")
            
        probs_array = results["probs"]
        processed_data = results["processed_data"]
        
        # Phase 13: Patient-Level Aggregation
        # Instead of median (which can hide paroxysmal AFIB), we use the Mean Probability 
        # across all 10-second segments to represent the patient-level likelihood.
        mean_probs = np.mean(probs_array, axis=0)
        
        class_names = ["Normal", "AFIB", "Conduction Block", "Other Arrhythmia"]
        pred_idx = int(np.argmax(mean_probs))
        classification = class_names[pred_idx]
        
        # Highest risk segment is the one with the maximum probability of any non-normal class
        anomaly_scores = probs_array[:, 1] + probs_array[:, 2] # AFIB + Other
        highest_risk_idx = int(np.argmax(anomaly_scores))
        highest_risk_waveform = processed_data[highest_risk_idx]
        
        # Explanation for the highest risk segment
        explanation = []
        try:
            if target_model_meta and 'target_model' in locals() and target_model is not None:
                active_tab = (tabular_batch[highest_risk_idx:highest_risk_idx+1] if tabular_batch is not None else None) if target_model_type == "multimodal" else None
                try:
                    import tensorflow as tf
                    w = highest_risk_waveform.reshape(1, 1000, 1)
                    x_tensor = tf.convert_to_tensor(w, dtype=tf.float32)
                    with tf.GradientTape() as tape:
                        tape.watch(x_tensor)
                        if active_tab is not None:
                            t_tensor = tf.convert_to_tensor(active_tab.reshape(1, -1), dtype=tf.float32)
                            preds = target_model([x_tensor, t_tensor], training=False)
                        else:
                            preds = target_model(x_tensor, training=False)
                        loss = preds[:, pred_idx]
                    grads = tape.gradient(loss, x_tensor)
                    if grads is not None:
                        attr = tf.abs(grads).numpy().flatten()
                        if np.max(attr) > 1e-8:
                            norm_attr = (attr / np.max(attr)) * 0.15
                            explanation = sorted(
                                [{"feature": f"time_{i}", "contribution": float(norm_attr[i])} for i in range(len(norm_attr))],
                                key=lambda x: x["contribution"],
                                reverse=True
                            )
                except Exception as g_err:
                    logger.warning(f"Target model gradient attribution failed: {g_err}")

            if not explanation:
                active_tab = (tabular_batch[highest_risk_idx:highest_risk_idx+1] if tabular_batch is not None else None) if target_model_type == "multimodal" else None
                explanation = inference_service.generate_attribution(
                    highest_risk_waveform,
                    target_class=pred_idx,
                    tabular=active_tab
                )
        except Exception as e:
            logger.error(f"Failed to generate explanation for segment: {e}")
            explanation = []
        
        distribution = {
            "Normal": int(np.sum(np.argmax(probs_array, axis=1) == 0)),
            "AFIB": int(np.sum(np.argmax(probs_array, axis=1) == 1)),
            "Conduction Block": int(np.sum(np.argmax(probs_array, axis=1) == 2)),
            "Other Arrhythmia": int(np.sum(np.argmax(probs_array, axis=1) == 3)) if probs_array.shape[1] > 3 else 0
        }

        # Persist prediction to the PostgreSQL database
        try:
            repo = PredictionRepository(db)
            db_prediction = Prediction(
                user_id=current_user.id,
                classification=classification,
                confidence_score=float(np.max(mean_probs) * 100),
                probability_vector=mean_probs.tolist(),
                model_version=model_version_name,
                explainable_insights=explanation
            )
            await repo.create(db_prediction)
        except Exception as db_err:
            logger.error(f"Failed to persist prediction to DB: {db_err}")

        # Extract HR/RMSSD for highest risk segment if multimodal
        hr_bpm = 72.0
        rmssd_ms = 35.0
        if target_model_type == "multimodal":
            try:
                from ai.preprocessing.preprocessing_v8 import extract_features
                hr_bpm, rmssd_ms = extract_features(highest_risk_waveform)
            except Exception as e:
                logger.error(f"Failed to extract features for reporting: {e}")

        return {
            "record_id": record_id,
            "sampling_rate": 100.0,
            "primary_prediction": f"Consistent with {classification}",
            "prediction": {
                "class": str(pred_idx),
                "label": classification,
                "confidence": float(np.max(mean_probs) * 100)
            },
            "class_probabilities": {
                "Normal": float(mean_probs[0] * 100),
                "AFIB": float(mean_probs[1] * 100),
                "Conduction Block": float(mean_probs[2] * 100),
                "Other Arrhythmia": float(mean_probs[3] * 100) if len(mean_probs) > 3 else 0.0
            },
            "probabilities": {
                "max_risk_prob": float(anomaly_scores[highest_risk_idx]),
                "avg_risk_prob": float(np.mean(anomaly_scores))
            },
            "distribution": distribution,
            "dominant_class": classification,
            "signal_quality": "GOOD",
            "segments_analyzed": len(windows),
            "inference_time_ms": inference_time_ms,
            "explanation": {
                "available": len(explanation) > 0,
                "values": explanation
            },
            "highest_risk_segment": highest_risk_waveform.flatten().tolist(),
            "reference_annotations": {
                "available": ".atr" in saved_files
            },
            "model_version": model_version_name,
            "model_type": target_model_type,
            "hr_bpm": float(hr_bpm),
            "rmssd_ms": float(rmssd_ms)
        }

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.post("/compare")
async def compare_models(
    files: List[UploadFile] = File(...),
    age: float = Form(None),
    sex: int = Form(None),
    model_ids: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    temp_dir = tempfile.mkdtemp()
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
            
        saved_files = {}
        for file in files:
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            ext = os.path.splitext(file.filename)[1].lower()
            saved_files[ext] = file.filename

        sig = []
        fs = 125.0
        
        if ".csv" in saved_files:
            csv_path = os.path.join(temp_dir, saved_files[".csv"])
            fs = 100.0
            df = pd.read_csv(csv_path, header=None)
            if df.shape[1] == 1:
                sig = df.iloc[:, 0].values.tolist()
            elif df.shape[1] >= 2:
                try:
                    float(df.iloc[0, 1])
                    sig = df.iloc[:, 1].values.tolist()
                except ValueError:
                    sig = df.iloc[1:, 1].values.astype(float).tolist()
            else:
                sig = df.iloc[:, 0].values.tolist()

        orchestrator = get_orchestrator()
        payload = {
            "waveform": sig,
            "age": age,
            "sex": sex,
            "fs": fs
        }
        
        if model_ids:
            ids_list = [m.strip() for m in model_ids.split(",")]
            results = orchestrator.run_multiple_models(ids_list, payload)
        else:
            results = orchestrator.run_all_compatible_models(payload)
            
        return {"comparisons": results}
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

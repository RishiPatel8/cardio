import os
import time
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


def resolve_wfdb_record_path(temp_dir: str, saved_files: dict):
    """
    Resolves WFDB record path in temp_dir, aliasing any mismatch between
    uploaded file names (e.g. 100(1).hea / 100(1).dat) and internal references in the header.
    Returns (record_path_for_wfdb, record_id).
    """
    hea_filename = saved_files.get(".hea")
    if not hea_filename:
        raise ValueError("Missing .hea header file")
        
    hea_path = os.path.join(temp_dir, hea_filename)
    
    with open(hea_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
    if not lines:
        raise ValueError("Invalid or empty .hea header file")
        
    rec_name_in_header = lines[0].split()[0]
    
    # Check referenced data files
    for line in lines[1:]:
        tokens = line.split()
        if tokens:
            expected_dat = tokens[0]
            expected_dat_path = os.path.join(temp_dir, expected_dat)
            if not os.path.exists(expected_dat_path):
                # Look for an uploaded .dat file in saved_files
                dat_filename = saved_files.get(".dat")
                if dat_filename:
                    src_dat = os.path.join(temp_dir, dat_filename)
                    if os.path.exists(src_dat):
                        shutil.copyfile(src_dat, expected_dat_path)
                        
    # Ensure header exists with rec_name_in_header
    rec_hea_path = os.path.join(temp_dir, f"{rec_name_in_header}.hea")
    if not os.path.exists(rec_hea_path):
        shutil.copyfile(hea_path, rec_hea_path)
        
    # Also ensure dat exists with rec_name_in_header.dat if needed
    rec_dat_path = os.path.join(temp_dir, f"{rec_name_in_header}.dat")
    if not os.path.exists(rec_dat_path) and saved_files.get(".dat"):
        shutil.copyfile(os.path.join(temp_dir, saved_files[".dat"]), rec_dat_path)
        
    # Check if .atr was uploaded and alias it
    if ".atr" in saved_files:
        atr_filename = saved_files[".atr"]
        rec_atr_path = os.path.join(temp_dir, f"{rec_name_in_header}.atr")
        if not os.path.exists(rec_atr_path):
            shutil.copyfile(os.path.join(temp_dir, atr_filename), rec_atr_path)
            
    return os.path.join(temp_dir, rec_name_in_header), rec_name_in_header


def extract_demographics_from_record(record, form_age: Optional[float], form_sex: Optional[int]):
    """
    Extracts age and sex from record comments if not provided in form.
    Pattern in MIT-BIH comments: e.g. '69 M 1085 1629 x1'
    """
    age = form_age
    sex = form_sex
    if record and hasattr(record, "comments") and record.comments:
        import re
        for comment in record.comments:
            if age is None or sex is None:
                match = re.search(r'(\d+)\s+([MFmf])', comment)
                if match:
                    if age is None:
                        age = float(match.group(1))
                    if sex is None:
                        sex = 0 if match.group(2).upper() == 'M' else 1
    return age, sex

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
            try:
                record_path, record_id = resolve_wfdb_record_path(temp_dir, saved_files)
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
                
                # Extract demographics from header comments if missing
                age, sex = extract_demographics_from_record(record, age, sex)
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
        target_model_id = model_id if (model_id and model_id != "default") else orchestrator.registry.get("active_model", "resnet")
        target_model_meta = orchestrator.registry.get("models", {}).get(target_model_id)
        model_id = target_model_id
        target_model_type = target_model_meta.get("input_type", "ecg") if target_model_meta else "ecg"
        model_version_name = target_model_meta.get("version", target_model_meta.get("id")) if target_model_meta else "v6-canonical"
        
        # --- SEVEN-MODEL ENSEMBLE EXECUTION PATH ---
        if target_model_id in ["v9_ensemble", "ensemble"] or target_model_type == "ensemble":
            from app.services.ensemble_service import get_ensemble_service, BASE_MODEL_ORDER
            ensemble_service = get_ensemble_service()
            
            ens_start_time = time.perf_counter()
            canonical_classes = ["Normal Sinus Rhythm", "Atrial Fibrillation", "Conduction Block", "Other Arrhythmia"]
            
            # Prepare tabular batch if age & sex are available
            tabular_batch = None
            if age is not None and sex is not None:
                try:
                    import sys
                    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))
                    from ai.preprocessing.preprocessing_v8 import build_tabular_tensor
                    tabular_list = [build_tabular_tensor(age, sex, w, fs=fs) for w in windows]
                    tabular_batch = np.array(tabular_list, dtype=np.float32)
                except Exception as ex:
                    logger.warning(f"Ensemble tabular tensor build warning: {ex}")
                    tabular_batch = None

            # Preprocess ECG windows
            pipeline = orchestrator.load_pipeline("resnet")
            if pipeline and pipeline.is_fitted:
                processed_w = pipeline.process_inference_data(windows, original_fs=fs)
            else:
                processed_w = windows
            waveform_data = processed_w.reshape(processed_w.shape[0], 1000, 1)

            individual_outputs = []
            segment_probs_list = []

            for mid in BASE_MODEL_ORDER:
                meta = orchestrator.registry.get("models", {}).get(mid, {})
                m_type = meta.get("input_type", "ecg")
                arch = meta.get("architecture", mid)
                m_ver = meta.get("version", mid)

                # Multimodal or Tabular requirements check
                if m_type in ["tabular", "multimodal"] and tabular_batch is None:
                    individual_outputs.append({
                        "model_id": mid,
                        "architecture": arch,
                        "model_version": m_ver,
                        "status": "failed: insufficient-input: Patient Age and Sex required",
                        "probabilities": {}
                    })
                    continue

                try:
                    m_start = time.perf_counter()
                    model = orchestrator.load_model(mid)
                    if m_type == "multimodal":
                        raw_probs = model.predict([waveform_data, tabular_batch], verbose=0)
                    elif m_type == "tabular":
                        raw_probs = model.predict(tabular_batch, verbose=0)
                    else:
                        raw_probs = model.predict(waveform_data, verbose=0)

                    m_latency = int((time.perf_counter() - m_start) * 1000)
                    m_mean_probs = np.mean(raw_probs, axis=0)
                    m_mean_probs = np.clip(m_mean_probs, 1e-7, 1.0)
                    m_mean_probs = m_mean_probs / np.sum(m_mean_probs)

                    m_pred_idx = int(np.argmax(m_mean_probs))
                    m_pred_class = canonical_classes[m_pred_idx]

                    segment_probs_list.append(raw_probs)
                    individual_outputs.append({
                        "model_id": mid,
                        "architecture": arch,
                        "model_version": m_ver,
                        "prediction": m_pred_class,
                        "classification": m_pred_class,
                        "confidence": float(m_mean_probs[m_pred_idx] * 100.0),
                        "probability_vector": m_mean_probs.tolist(),
                        "latency_ms": m_latency,
                        "status": "success"
                    })
                except Exception as m_err:
                    individual_outputs.append({
                        "model_id": mid,
                        "architecture": arch,
                        "model_version": m_ver,
                        "status": f"failed: {m_err}",
                        "probabilities": {}
                    })

            ensemble_res = ensemble_service.aggregate_predictions(individual_outputs)
            total_latency = int((time.perf_counter() - ens_start_time) * 1000)

            final_probs = np.array(ensemble_res["probability_vector"])
            pred_idx = ensemble_res["class_index"]
            classification = ensemble_res["classification"]

            # Segment distribution & highest risk segment
            if segment_probs_list:
                mean_seg_probs = np.mean(segment_probs_list, axis=0)
                anomaly_scores = mean_seg_probs[:, 1] + mean_seg_probs[:, 2] + mean_seg_probs[:, 3]
                highest_risk_idx = int(np.argmax(anomaly_scores))
                highest_risk_waveform = processed_w[highest_risk_idx]
                distribution = {
                    "Normal": int(np.sum(np.argmax(mean_seg_probs, axis=1) == 0)),
                    "AFIB": int(np.sum(np.argmax(mean_seg_probs, axis=1) == 1)),
                    "Conduction Block": int(np.sum(np.argmax(mean_seg_probs, axis=1) == 2)),
                    "Other Arrhythmia": int(np.sum(np.argmax(mean_seg_probs, axis=1) == 3))
                }
            else:
                highest_risk_idx = 0
                highest_risk_waveform = processed_w[0] if len(processed_w) > 0 else np.zeros((1000, 1))
                distribution = { "Normal": 0, "AFIB": 0, "Conduction Block": 0, "Other Arrhythmia": 0 }

            explanation = []
            try:
                grad_model = orchestrator.load_model("v7_resnet")
                import tensorflow as tf
                w = highest_risk_waveform.reshape(1, 1000, 1)
                x_tensor = tf.convert_to_tensor(w, dtype=tf.float32)
                with tf.GradientTape() as tape:
                    tape.watch(x_tensor)
                    preds = grad_model(x_tensor, training=False)
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
            except Exception as exp_err:
                logger.warning(f"Ensemble saliency attribution warning: {exp_err}")

            try:
                repo = PredictionRepository(db)
                db_prediction = Prediction(
                    user_id=current_user.id,
                    classification=classification,
                    confidence_score=float(ensemble_res["confidence"]),
                    probability_vector=ensemble_res["probability_vector"],
                    model_version="v9-ensemble",
                    explainable_insights=explanation
                )
                await repo.create(db_prediction)
            except Exception as db_err:
                logger.error(f"Failed to persist ensemble prediction to DB: {db_err}")

            hr_bpm = 72.0
            rmssd_ms = 35.0
            try:
                from ai.preprocessing.preprocessing_v8 import extract_features
                hr_bpm, rmssd_ms = extract_features(highest_risk_waveform)
            except Exception as e:
                logger.error(f"Failed to extract features for reporting: {e}")

            return {
                "record_id": record_id,
                "sampling_rate": 100.0,
                "resultType": classification,
                "confidence": float(ensemble_res["confidence"]),
                "modelVersion": "v9-ensemble",
                "primary_prediction": f"Consistent with {classification}",
                "prediction": {
                    "class": str(pred_idx),
                    "label": classification,
                    "confidence": float(ensemble_res["confidence"])
                },
                "class_probabilities": ensemble_res["class_probabilities"],
                "probability_vector": ensemble_res["probability_vector"],
                "contributing_models_count": ensemble_res["contributing_models_count"],
                "total_models_count": ensemble_res["total_models_count"],
                "contributing_models": ensemble_res["contributing_models"],
                "excluded_models": ensemble_res["excluded_models"],
                "ensemble_weights": ensemble_res["ensemble_weights"],
                "agreement_analysis": ensemble_res["agreement_analysis"],
                "probabilities": {
                    "max_risk_prob": float(np.max(final_probs[1:])),
                    "avg_risk_prob": float(np.mean(final_probs[1:]))
                },
                "distribution": distribution,
                "dominant_class": classification,
                "signal_quality": "GOOD",
                "segments_analyzed": len(windows),
                "inference_time_ms": total_latency,
                "explanation": {
                    "available": len(explanation) > 0,
                    "values": explanation
                },
                "highest_risk_segment": highest_risk_waveform.flatten().tolist(),
                "reference_annotations": {
                    "available": ".atr" in saved_files
                },
                "model_version": "v9-ensemble",
                "model_type": "ensemble",
                "hr_bpm": float(hr_bpm),
                "rmssd_ms": float(rmssd_ms)
            }
        
        tabular_batch = None
        if target_model_type in ["multimodal", "tabular"]:
            if age is None or sex is None:
                raise HTTPException(
                    status_code=400,
                    detail="insufficient-input: Patient Age and Sex are required for multimodal/tabular inference and could not be determined from the file."
                )
            try:
                import sys
                sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))
                from ai.preprocessing.preprocessing_v8 import build_tabular_tensor
                tabular_list = []
                for w in windows:
                    tab = build_tabular_tensor(age, sex, w, fs=fs)
                    tabular_list.append(tab)
                tabular_batch = np.array(tabular_list, dtype=np.float32)
            except Exception as e:
                logger.error(f"Failed to build tabular batch: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to preprocess tabular data: {str(e)}")
        
        # Batch inference
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
        
        # Patient-Level Aggregation across all 10-second segments
        mean_probs = np.mean(probs_array, axis=0)
        mean_probs = np.clip(mean_probs, 1e-7, 1.0)
        mean_probs = mean_probs / np.sum(mean_probs)
        
        canonical_classes = ["Normal Sinus Rhythm", "Atrial Fibrillation", "Conduction Block", "Other Arrhythmia"]
        pred_idx = int(np.argmax(mean_probs))
        classification = canonical_classes[pred_idx]
        
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
                "Normal Sinus Rhythm": float(mean_probs[0] * 100),
                "Normal": float(mean_probs[0] * 100),
                "Atrial Fibrillation": float(mean_probs[1] * 100),
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
        fs = 100.0
        
        if ".csv" in saved_files:
            csv_path = os.path.join(temp_dir, saved_files[".csv"])
            df = pd.read_csv(csv_path, header=None)
            if df.shape[1] == 1:
                sig = pd.to_numeric(df.iloc[:, 0], errors="coerce").dropna().values.tolist()
            elif df.shape[1] >= 2:
                sig = pd.to_numeric(df.iloc[:, 1], errors="coerce").dropna().values.tolist()
            else:
                sig = pd.to_numeric(df.iloc[:, 0], errors="coerce").dropna().values.tolist()

        elif ".hea" in saved_files and ".dat" in saved_files:
            try:
                record_path, record_id = resolve_wfdb_record_path(temp_dir, saved_files)
                record = wfdb.rdrecord(record_path)
                raw_sig = record.p_signal[:, 0]
                orig_fs = record.fs
                if orig_fs != 100.0:
                    num_samples = int(len(raw_sig) * (100.0 / orig_fs))
                    raw_sig = scipy.signal.resample(raw_sig, num_samples)
                sig = raw_sig.tolist()
                fs = 100.0
                age, sex = extract_demographics_from_record(record, age, sex)
            except Exception as e:
                logger.error(f"Failed to parse WFDB record in compare: {e}")
                raise HTTPException(status_code=400, detail=f"Failed to parse WFDB record: {str(e)}")

        elif ".dat" in saved_files and len(saved_files) == 1:
            dat_path = os.path.join(temp_dir, saved_files[".dat"])
            try:
                sig = np.fromfile(dat_path, dtype=np.int16).astype(float).tolist()
            except Exception:
                sig = pd.read_csv(dat_path, header=None).iloc[:, 0].dropna().values.tolist()

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


@router.post("/ensemble", summary="Run Seven-Model Ensemble on Uploaded ECG Files")
async def analyze_physionet_ensemble(
    files: List[UploadFile] = File(...),
    age: float = Form(None),
    sex: int = Form(None),
    current_user: User = Depends(get_current_user),
    inference_service: InferenceService = Depends(get_inference_service),
    db: AsyncSession = Depends(get_db)
):
    """Executes the Seven-Model Weighted Soft-Voting Ensemble on uploaded ECG files."""
    return await analyze_physionet(
        files=files,
        age=age,
        sex=sex,
        model_id="v9_ensemble",
        current_user=current_user,
        inference_service=inference_service,
        db=db
    )

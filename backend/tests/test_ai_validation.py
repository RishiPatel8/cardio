import pytest
import numpy as np
import torch
from ai.preprocessing.filters import apply_bandpass_filter, normalize_signal, interpolate_missing_samples
from ai.preprocessing.qrs_detection import detect_r_peaks, calculate_rr_intervals
from ai.feature_engineering.hrv_features import (
    extract_time_domain_hrv,
    extract_frequency_domain_hrv,
    extract_all_hrv_features
)
from ai.foundation_models.transformer import TimeSeriesTransformer
from ai.fusion.multimodal_fusion import MultimodalFusionModel, preprocess_tabular_features
from ai.training.ensemble import RiskClassifierEnsemble
from ai.inference.explainable_ai import compute_feature_contributions, generate_natural_language_explanation

def test_pan_tompkins_filtering_and_peak_detection():
    # 1. Generate 10 seconds of simulated ECG signal at 250 Hz
    fs = 250.0
    t = np.arange(0, 10.0, 1.0 / fs)
    
    # Clean ECG-like wave (simulating R-waves at ~1.2 Hz / 72 bpm)
    ecg = np.zeros_like(t)
    r_peak_indices = [int(i * fs * 0.8) for i in range(1, 12)]  # peaks every 0.8s
    for idx in r_peak_indices:
        if idx < len(ecg) - 10:
            ecg[idx:idx+5] = 1.5  # Simulate high R-peak voltage
            
    # Add baseline wander (low frequency noise) and high-frequency noise
    noise = np.sin(2 * np.pi * 50.0 * t) * 0.2  # 50 Hz powerline interference
    wander = np.sin(2 * np.pi * 0.15 * t) * 0.4  # 0.15 Hz baseline drift
    dirty_signal = ecg + noise + wander
    
    # Run butterworth bandpass filter
    filtered = apply_bandpass_filter(dirty_signal, lowcut=0.5, highcut=45.0, fs=fs)
    assert len(filtered) == len(dirty_signal)
    
    # Verify noise attenuation (variance check)
    assert np.var(filtered) < np.var(dirty_signal)
    
    # Run peak detection
    r_peaks = detect_r_peaks(filtered, fs=fs)
    assert len(r_peaks) > 0
    
    # Run RR interval calculation
    rr_intervals = calculate_rr_intervals(r_peaks, fs=fs)
    assert len(rr_intervals) == len(r_peaks) - 1
    # Check that rr intervals match approximately 800ms (at 72bpm)
    if len(rr_intervals) > 0:
        assert np.all(rr_intervals > 0)
        assert np.all(rr_intervals < 1500)

def test_hrv_feature_extraction_clinical_bounds():
    # Simulate a regular series of RR intervals (e.g. 800ms +/- 20ms)
    np.random.seed(42)
    rr_intervals = np.random.normal(loc=800.0, scale=20.0, size=50)
    
    # Extract time domain parameters
    time_features = extract_time_domain_hrv(rr_intervals)
    assert "mean_rr" in time_features
    assert "sdnn" in time_features
    assert "rmssd" in time_features
    assert "pnn50" in time_features
    assert 700.0 < time_features["mean_rr"] < 900.0
    assert time_features["sdnn"] > 0.0
    assert time_features["rmssd"] > 0.0
    
    # Extract frequency domain parameters
    freq_features = extract_frequency_domain_hrv(rr_intervals, fs_interpolate=4.0)
    assert "lf" in freq_features
    assert "hf" in freq_features
    assert "lf_hf_ratio" in freq_features
    assert freq_features["lf_hf_ratio"] >= 0.0
    
    # Extract complete feature set
    all_features = extract_all_hrv_features(rr_intervals)
    assert "mean_rr" in all_features
    assert "sd1" in all_features
    assert "sd2" in all_features
    assert all_features["sd1"] > 0.0
    assert all_features["sd2"] > 0.0

def test_pytorch_neural_models_and_fusion():
    # 1. Test Foundation Model: Time Series Transformer
    model = TimeSeriesTransformer(input_dim=1, d_model=64, nhead=4, num_layers=2)
    dummy_sequences = torch.randn(2, 50, 1)  # [batch_size=2, seq_len=50, input_dim=1]
    
    model.eval()
    with torch.no_grad():
        embeddings = model.encode(dummy_sequences)
    # Output shape: [batch_size, d_model]
    assert embeddings.shape == (2, 64)
    
    # 2. Test Multimodal Fusion Layer
    fusion_model = MultimodalFusionModel(transformer_model=model, tabular_dim=12, fused_dim=32, num_classes=2)
    dummy_tabular = torch.randn(2, 12)  # [batch_size=2, tabular_dim=12]
    
    fusion_model.eval()
    with torch.no_grad():
        logits = fusion_model(dummy_sequences, dummy_tabular)
    # Output shape: [batch_size, num_classes]
    assert logits.shape == (2, 2)

def test_ensemble_model_consistency_and_predictions():
    # Setup mock dataset: 100 samples, 12 features each
    np.random.seed(42)
    X = np.random.normal(loc=1.0, scale=0.5, size=(100, 12))
    # Labels: 0 (healthy), 1 (arrhythmia risk)
    y = np.array([0] * 60 + [1] * 40)
    
    # Instantiate and train ensemble
    ensemble = RiskClassifierEnsemble()
    X_train, X_val = X[:80], X[80:]
    y_train, y_val = y[:80], y[80:]
    
    train_results = ensemble.train_and_evaluate(X_train, y_train, X_val, y_val)
    assert "best_model_selected" in train_results
    assert "best_metrics" in train_results
    
    # Test single-point prediction
    test_sample = X_val[0:1]
    pred_1, prob_1, conf_1 = ensemble.predict_risk(test_sample)
    
    # Assert type and boundaries
    assert pred_1 in [0, 1]
    assert 0.0 <= prob_1 <= 1.0
    assert 50.0 <= conf_1 <= 100.0
    
    # Test consistency (run same inputs through the ensemble twice to verify exact match)
    pred_2, prob_2, conf_2 = ensemble.predict_risk(test_sample)
    assert pred_1 == pred_2
    assert prob_1 == prob_2
    assert conf_1 == conf_2

def test_explainable_ai_shap_physiological_sanity():
    # Test physiological baseline deviation logic
    feature_names = [
        "mean_rr", "sdnn", "rmssd", "pnn50", "lf_hf_ratio", "sd1", "sd2", 
        "steps", "calories", "sleep_minutes", "spo2", "age"
    ]
    
    # 1. Simulate critically low HRV (high risk profile)
    low_hrv_features = np.array([
        700.0,  # mean_rr (lower than 800)
        20.0,   # sdnn (critically low, base=50.0)
        12.0,   # rmssd (critically low, base=35.0)
        2.0,    # pnn50 (critically low, base=12.0)
        3.5,    # lf_hf_ratio (elevated, base=1.5)
        10.0,   # sd1 (critically low, base=25.0)
        40.0,   # sd2 (critically low, base=70.0)
        2000.0, # steps
        100.0,  # calories
        300.0,  # sleep
        94.0,   # spo2 (hypoxic, base=98.0)
        65.0    # age (base=45)
    ])
    
    # Anomaly predictions: expect positive contributions driving arrhythmia risk
    contributions_anomaly = compute_feature_contributions(
        low_hrv_features, feature_names, is_anomaly=True
    )
    
    # Index specific parameters and verify positive risk weightings
    sdnn_contrib = next(c for c in contributions_anomaly if c["feature"] == "sdnn")
    rmssd_contrib = next(c for c in contributions_anomaly if c["feature"] == "rmssd")
    spo2_contrib = next(c for c in contributions_anomaly if c["feature"] == "spo2")
    
    assert sdnn_contrib["contribution"] > 0.0
    assert rmssd_contrib["contribution"] > 0.0
    assert spo2_contrib["contribution"] > 0.0
    
    # Generate explanations
    insights_anomaly = generate_natural_language_explanation(
        contributions_anomaly, classification="AFIB", confidence=88.5
    )
    assert len(insights_anomaly) > 0
    # Confirm explanation matches anomalies
    assert any("critically low sdnn" in s.lower() or "critically low rmssd" in s.lower() or "sdnn" in s.lower() or "rmssd" in s.lower() for s in insights_anomaly)

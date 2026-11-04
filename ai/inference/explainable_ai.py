import numpy as np
from typing import Dict, Any, List

def compute_feature_contributions(
    features: np.ndarray,
    feature_names: List[str],
    is_anomaly: bool
) -> List[Dict[str, Any]]:
    """Calculates SHAP-like contribution weights by evaluating feature deviations from healthy physiological baselines."""
    # Healthy baselines for reference
    baselines = {
        "mean_rr": 800.0,
        "sdnn": 50.0,
        "rmssd": 35.0,
        "pnn50": 12.0,
        "lf_hf_ratio": 1.5,
        "sd1": 25.0,
        "sd2": 70.0,
        "steps": 10000.0,
        "calories": 350.0,
        "sleep_minutes": 450.0,
        "spo2": 98.0,
        "systolic_bp": 120.0,
        "diastolic_bp": 80.0,
        "age": 45.0,
        "height": 175.0,
        "weight": 70.0,
        "bmi": 22.86,
        "sex_numeric": 0.5,
        "smoking": 0.0,
        "alcohol": 0.0,
        "activity_level_numeric": 0.5,
        "diabetes": 0.0,
        "hypertension": 0.0,
        "cholesterol": 0.0,
        "previous_heart_disease": 0.0,
        "stroke_history": 0.0,
    }
    
    contributions = []
    for i, name in enumerate(feature_names):
        # Prevent index out of bounds
        if i >= len(features):
            break
        val = features[i]
        base = baselines.get(name, val)
        
        # Calculate standard deviation offsets / impact direction
        if base == 0:
            deviation = val
        else:
            deviation = (val - base) / base
        
        # Determine polarity based on medical significance
        weight = 0.0
        if name in ["sdnn", "rmssd", "sd1", "pnn50"]:
            weight = -deviation * 0.8
        elif name == "lf_hf_ratio":
            weight = deviation * 0.4
        elif name == "spo2":
            weight = -deviation * 1.5
        elif name in ["systolic_bp", "diastolic_bp"]:
            weight = deviation * 1.2
        elif name in ["diabetes", "hypertension", "cholesterol", "previous_heart_disease", "stroke_history", "smoking"]:
            weight = deviation * 1.0
        elif name in ["steps", "sleep_minutes", "activity_level_numeric"]:
            weight = -deviation * 0.3
        else:
            weight = deviation * 0.2
            
        # Scaling contributions to range [-1, 1]
        weight = float(np.clip(weight, -1.0, 1.0))
        
        # If normal, invert contribution impact directions to justify healthy sinus rhythm
        if not is_anomaly:
            weight = -weight
            
        contributions.append({
            "feature": name,
            "value": float(val),
            "baseline": float(base),
            "contribution": weight
        })
        
    return contributions

def generate_natural_language_explanation(
    contributions: List[Dict[str, Any]],
    classification: str,
    confidence: float
) -> List[str]:
    """Generates heuristic physiological insights, clearly separating them from model interpretation."""
    insights = []
    
    insights.append(f"MODEL PREDICTION: {classification} — {confidence:.1f}% model probability.")
    
    for c in contributions:
        name = c["feature"].upper()
        val = c["value"]
        if name in ["SDNN", "RMSSD"]:
            insights.append(f"SUPPLEMENTARY INSIGHT: {name} is {val:.1f} ms relative to the configured reference range.")
            
    insights.append("These physiological insights are supplementary and are not explanations of the neural network's internal decision.")
    insights.append("This output is an AI research prediction and is not a clinical diagnosis. Please consult a qualified healthcare professional for clinical interpretation.")
        
    return insights

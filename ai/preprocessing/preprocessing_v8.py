import numpy as np
from scipy.signal import find_peaks

def extract_features(signal: np.ndarray, fs: float = 100.0):
    """
    Extracts HR and RMSSD from an ECG signal exactly as implemented during V8 training.
    """
    sig = signal.flatten()
    
    # 1. Heart Rate (HR)
    # Simple peak detection for R-peaks
    # Distance of at least 0.4s (assuming max HR ~ 150 bpm)
    # Height threshold: using a simple heuristic based on signal max
    peaks, _ = find_peaks(sig, distance=int(0.4 * fs), height=np.max(sig) * 0.4)
    
    if len(peaks) < 2:
        return 75.0, 0.0 # Fallback
        
    rr_intervals = np.diff(peaks) / fs  # in seconds
    hr = 60.0 / np.mean(rr_intervals)
    
    # 2. HRV (RMSSD)
    if len(rr_intervals) < 2:
        rmssd = 0.0
    else:
        rr_diff = np.diff(rr_intervals)
        rmssd = np.sqrt(np.mean(rr_diff**2)) * 1000.0 # in ms
        
    return hr, rmssd

def build_tabular_tensor(age: float, sex: int, signal: np.ndarray, fs: float = 100.0) -> np.ndarray:
    """
    Builds the tabular tensor exactly as required by V8 TCN Multimodal.
    Order MUST be: [age_norm, sex, hr_norm, rmssd_norm]
    """
    hr, rmssd = extract_features(signal, fs)
    
    age_norm = age / 100.0
    hr_norm = hr / 200.0
    rmssd_norm = rmssd / 150.0
    
    return np.array([age_norm, float(sex), hr_norm, rmssd_norm], dtype=np.float32)

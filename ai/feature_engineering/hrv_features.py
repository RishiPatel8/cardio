import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import welch
from typing import Dict, Any

def extract_time_domain_hrv(rr_intervals: np.ndarray) -> Dict[str, float]:
    """Extracts standard clinical time-domain heart rate variability parameters."""
    if len(rr_intervals) < 2:
        return {
            "mean_rr": 0.0,
            "sdnn": 0.0,
            "rmssd": 0.0,
            "pnn50": 0.0,
            "mean_hr": 0.0
        }
        
    diff_rr = np.diff(rr_intervals)
    mean_rr = np.mean(rr_intervals)
    sdnn = np.std(rr_intervals, ddof=1)
    rmssd = np.sqrt(np.mean(diff_rr ** 2))
    
    nn50 = np.sum(np.abs(diff_rr) > 50.0)
    pnn50 = (nn50 / len(diff_rr)) * 100.0 if len(diff_rr) > 0 else 0.0
    
    mean_hr = 60000.0 / mean_rr if mean_rr > 0 else 0.0
    
    return {
        "mean_rr": float(mean_rr),
        "sdnn": float(sdnn),
        "rmssd": float(rmssd),
        "pnn50": float(pnn50),
        "mean_hr": float(mean_hr)
    }

def extract_frequency_domain_hrv(rr_intervals: np.ndarray, fs_interpolate: float = 4.0) -> Dict[str, float]:
    """Resamples RR intervals to regularly sampled intervals and runs Welch's method for frequency power bands."""
    if len(rr_intervals) < 10:
        return {"lf": 0.0, "hf": 0.0, "lf_hf_ratio": 0.0}
        
    # Generate timestamp coordinates for intervals
    times = np.cumsum(rr_intervals) / 1000.0 # coordinates in seconds
    times = times - times[0]
    
    # Resample at regularly spaced grids
    f_interp = interp1d(times, rr_intervals, kind='linear', fill_value="extrapolate")
    new_times = np.arange(times[0], times[-1], 1.0 / fs_interpolate)
    
    if len(new_times) < 10:
        return {"lf": 0.0, "hf": 0.0, "lf_hf_ratio": 0.0}
        
    rr_resampled = f_interp(new_times)
    
    # Run Welch periodogram
    nperseg = min(len(rr_resampled), 256)
    freqs, psd = welch(rr_resampled, fs=fs_interpolate, nperseg=nperseg)
    
    # Spectral power integrations
    lf_band = (0.04, 0.15)
    hf_band = (0.15, 0.40)
    
    lf_idx = np.logical_and(freqs >= lf_band[0], freqs <= lf_band[1])
    hf_idx = np.logical_and(freqs >= hf_band[0], freqs <= hf_band[1])
    
    lf_power = np.trapz(psd[lf_idx], freqs[lf_idx]) if np.any(lf_idx) else 0.0
    hf_power = np.trapz(psd[hf_idx], freqs[hf_idx]) if np.any(hf_idx) else 0.0
    
    lf_hf_ratio = lf_power / hf_power if hf_power > 0 else 0.0
    
    return {
        "lf": float(lf_power),
        "hf": float(hf_power),
        "lf_hf_ratio": float(lf_hf_ratio)
    }

def extract_poincare_hrv(rr_intervals: np.ndarray) -> Dict[str, float]:
    """Calculates non-linear Poincaré plot descriptors (SD1, SD2, ratio)."""
    if len(rr_intervals) < 3:
        return {"sd1": 0.0, "sd2": 0.0, "sd1_sd2_ratio": 0.0}
        
    x = rr_intervals[:-1]
    y = rr_intervals[1:]
    
    sd1 = np.sqrt(0.5 * np.std(x - y, ddof=1) ** 2)
    sd2 = np.sqrt(0.5 * np.std(x + y, ddof=1) ** 2)
    
    sd1_sd2_ratio = sd1 / sd2 if sd2 > 0 else 0.0
    
    return {
        "sd1": float(sd1),
        "sd2": float(sd2),
        "sd1_sd2_ratio": float(sd1_sd2_ratio)
    }

def extract_all_hrv_features(rr_intervals: np.ndarray) -> Dict[str, float]:
    """Extracts all time-domain, frequency-domain, and non-linear HRV parameters."""
    features = {}
    features.update(extract_time_domain_hrv(rr_intervals))
    features.update(extract_frequency_domain_hrv(rr_intervals))
    features.update(extract_poincare_hrv(rr_intervals))
    return features

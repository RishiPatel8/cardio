import numpy as np

def assess_signal_quality(signal, threshold_flat=0.01, threshold_clip=2.0):
    """
    Assesses whether a 1000-sample ECG signal is of sufficient quality for inference.
    
    Returns:
        is_valid (bool): True if signal is acceptable
        reason (str): Explanation if invalid, otherwise "OK"
    """
    # 1. Flatline check
    if np.std(signal) < threshold_flat:
        return False, "Signal is mostly flat (low variance)."
        
    # 2. Clipping/saturation check
    max_val = np.max(np.abs(signal))
    if max_val > threshold_clip:
        # Check if too many samples are stuck at max
        num_clipped = np.sum(np.abs(signal) > threshold_clip * 0.95)
        if num_clipped > 0.1 * len(signal):
            return False, "Signal contains significant clipping/saturation artifacts."
            
    # 3. NaN/Inf check
    if np.isnan(signal).any() or np.isinf(signal).any():
        return False, "Signal contains NaN or Inf values."
        
    # 4. Extreme noise/variance check
    if np.var(signal) > 10.0:
        return False, "Signal variance is extremely high (severe noise)."
        
    # 5. Zero-crossing rate check (too high = pure high-frequency noise)
    zero_crossings = np.where(np.diff(np.signbit(signal)))[0]
    zcr = len(zero_crossings) / len(signal)
    if zcr > 0.4:
        return False, "Signal zero-crossing rate is excessively high (pure noise)."
        
    return True, "OK"

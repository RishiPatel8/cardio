import numpy as np
from scipy.signal import find_peaks
from typing import List, Tuple

def detect_r_peaks(signal: np.ndarray, fs: float) -> np.ndarray:
    """Detects R-peaks using amplitude, derivative, and minimum refractory period constraints."""
    # Step 1: Derivative filter to enhance QRS complexes
    derivative = np.diff(signal)
    
    # Step 2: Squaring to amplify high slopes
    squared = derivative ** 2
    
    # Step 3: Moving integration window (approx 150ms window)
    window_len = int(0.15 * fs)
    integrated = np.convolve(squared, np.ones(window_len)/window_len, mode='same')
    
    # Step 4: Find peaks with physiological limits (HR max 200 bpm = min 300ms refractory period)
    min_distance = int(0.3 * fs)
    prominence = np.std(integrated) * 0.5
    
    peaks, _ = find_peaks(integrated, distance=min_distance, prominence=prominence)
    
    # Map back peaks from integrated to original signal local maxima
    refined_peaks = []
    search_window = int(0.05 * fs) # 50ms search window around peak
    for p in peaks:
        start = max(0, p - search_window)
        end = min(len(signal), p + search_window)
        if start < end:
            r_peak = start + np.argmax(signal[start:end])
            refined_peaks.append(r_peak)
            
    return np.array(refined_peaks)

def calculate_rr_intervals(r_peaks: np.ndarray, fs: float) -> np.ndarray:
    """Converts R-peak sample coordinates into beat-to-beat (RR) intervals in milliseconds."""
    if len(r_peaks) < 2:
        return np.array([])
    # diff in samples converted to seconds, then to milliseconds
    return (np.diff(r_peaks) / fs) * 1000.0

def segment_beats(signal: np.ndarray, r_peaks: np.ndarray, fs: float, before_ms: float = 200.0, after_ms: float = 400.0) -> List[np.ndarray]:
    """Segments individual cardiac beats centered on R-peaks."""
    before_samples = int((before_ms / 1000.0) * fs)
    after_samples = int((after_ms / 1000.0) * fs)
    
    segments = []
    for r in r_peaks:
        start = r - before_samples
        end = r + after_samples
        if start >= 0 and end <= len(signal):
            segments.append(signal[start:end])
            
    return segments

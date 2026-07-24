import numpy as np
from scipy.signal import butter, filtfilt, iirnotch

def butter_bandpass(lowcut: float, highcut: float, fs: float, order: int = 4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def apply_bandpass_filter(data: np.ndarray, lowcut: float, highcut: float, fs: float, order: int = 4) -> np.ndarray:
    """Applies a zero-phase Butterworth bandpass filter to remove noise outside cardiac frequency bands."""
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    return filtfilt(b, a, data)

def apply_notch_filter(data: np.ndarray, cutoff: float, fs: float, q: float = 30.0) -> np.ndarray:
    """Applies a notch filter to remove powerline interference (typically 50Hz or 60Hz)."""
    nyq = 0.5 * fs
    w0 = cutoff / nyq
    b, a = iirnotch(w0, q)
    return filtfilt(b, a, data)

def remove_baseline_wander(data: np.ndarray, fs: float) -> np.ndarray:
    """Removes baseline wander by subtracting a median-filtered representation (moving baseline correction)."""
    # 200ms and 600ms median filters for baseline estimation
    win1 = int(0.2 * fs)
    if win1 % 2 == 0: win1 += 1
    win2 = int(0.6 * fs)
    if win2 % 2 == 0: win2 += 1
    
    from scipy.ndimage import median_filter
    baseline = median_filter(data, size=win1)
    baseline = median_filter(baseline, size=win2)
    return data - baseline

def smooth_signal(data: np.ndarray, window_size: int = 5) -> np.ndarray:
    """Reduces high-frequency motion artifacts using a simple moving average window."""
    if window_size < 3:
        return data
    return np.convolve(data, np.ones(window_size)/window_size, mode='same')

def normalize_signal(data: np.ndarray, method: str = "zscore") -> np.ndarray:
    """Normalizes raw signal coordinates via z-score or min-max bounds."""
    if method == "minmax":
        dmin, dmax = np.min(data), np.max(data)
        if dmax - dmin == 0:
            return np.zeros_like(data)
        return (data - dmin) / (dmax - dmin)
    else:
        std = np.std(data)
        if std == 0:
            return np.zeros_like(data)
        return (data - np.mean(data)) / std

def interpolate_missing_samples(data: np.ndarray) -> np.ndarray:
    """Interpolates NaN/missing records in physiological telemetry sequences."""
    nans = np.isnan(data)
    if not np.any(nans):
        return data
    x = lambda z: z.nonzero()[0]
    data_clean = data.copy()
    data_clean[nans] = np.interp(x(nans), x(~nans), data[~nans])
    return data_clean

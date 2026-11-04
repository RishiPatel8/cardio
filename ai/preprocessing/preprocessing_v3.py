import numpy as np
import scipy.signal
from sklearn.preprocessing import StandardScaler
import joblib

class PreprocessingPipelineV3:
    """
    V3 Preprocessing Pipeline ensuring strict parity between training and inference.
    """
    def __init__(self, target_fs: float = 100.0, target_length: int = 1000):
        self.target_fs = target_fs
        self.target_length = target_length
        self.scaler = StandardScaler()
        self.is_fitted = False
        
    def _bandpass_filter(self, signal: np.ndarray, fs: float) -> np.ndarray:
        """Apply 0.5 - 45 Hz bandpass filter."""
        nyquist = 0.5 * fs
        low = 0.5 / nyquist
        high = 45.0 / nyquist
        b, a = scipy.signal.butter(3, [low, high], btype='band')
        return scipy.signal.filtfilt(b, a, signal)
        
    def _resample(self, signal: np.ndarray, original_fs: float) -> np.ndarray:
        """Resample to target frequency."""
        if original_fs == self.target_fs:
            return signal
        num_samples = int(len(signal) * self.target_fs / original_fs)
        return scipy.signal.resample(signal, num_samples)
        
    def _pad_or_truncate(self, signal: np.ndarray) -> np.ndarray:
        """Ensure exact target length."""
        if len(signal) > self.target_length:
            return signal[:self.target_length]
        elif len(signal) < self.target_length:
            return np.pad(signal, (0, self.target_length - len(signal)), 'constant')
        return signal

    def process_raw_segment(self, signal: np.ndarray, original_fs: float) -> np.ndarray:
        """
        Process a single raw segment BEFORE scaling.
        Includes resampling, filtering, and length alignment.
        """
        # Handle NaNs/Infs
        if np.isnan(signal).any() or np.isinf(signal).any():
            signal = np.nan_to_num(signal)
            
        resampled = self._resample(signal, original_fs)
        filtered = self._bandpass_filter(resampled, self.target_fs)
        aligned = self._pad_or_truncate(filtered)
        return aligned

    def fit(self, X_raw: np.ndarray, original_fs: float = 100.0):
        """Fit scaler on training data."""
        processed_list = []
        for sig in X_raw:
            processed_list.append(self.process_raw_segment(sig, original_fs))
            
        X_processed = np.array(processed_list)
        
        # Flatten for StandardScaling (N, 1000)
        shape_2d = X_processed.reshape(-1, X_processed.shape[-1])
        self.scaler.fit(shape_2d)
        self.is_fitted = True
        return self
        
    def transform(self, X_raw: np.ndarray, original_fs: float = 100.0) -> np.ndarray:
        """Transform data using fitted scaler."""
        if not self.is_fitted:
            raise ValueError("Pipeline not fitted.")
            
        processed_list = []
        for sig in X_raw:
            processed_list.append(self.process_raw_segment(sig, original_fs))
            
        X_processed = np.array(processed_list)
        shape_2d = X_processed.reshape(-1, X_processed.shape[-1])
        scaled = self.scaler.transform(shape_2d)
        
        # Return as (N, 1000) - expanding dims to (N, 1000, 1) happens in the model loop
        return scaled.reshape(X_processed.shape)

    def process_training_data(self, X_train: np.ndarray, original_fs: float = 100.0) -> np.ndarray:
        """Fit and transform training data."""
        self.fit(X_train, original_fs)
        return self.transform(X_train, original_fs)
        
    def process_inference_data(self, X_infer: np.ndarray, original_fs: float = 100.0) -> np.ndarray:
        """Transform inference data."""
        return self.transform(X_infer, original_fs)
        
    def save(self, filepath: str):
        joblib.dump(self.scaler, filepath)
        
    def load(self, filepath: str):
        self.scaler = joblib.load(filepath)
        self.is_fitted = True

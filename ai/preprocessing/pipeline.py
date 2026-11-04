import numpy as np
import pandas as pd
from scipy import signal
from sklearn.preprocessing import StandardScaler

class PreprocessingPipeline:
    def __init__(self, sampling_rate=100, window_size=1000): # PTB-XL standard window size for 10s at 100Hz is 1000
        self.sampling_rate = sampling_rate
        self.window_size = window_size
        self.scaler = StandardScaler()
        self.is_fitted = False

    def handle_missing_values(self, data: np.ndarray) -> np.ndarray:
        """Fill missing values using forward fill, then backward fill."""
        df = pd.DataFrame(data)
        df = df.ffill().bfill()
        return df.values

    def apply_bandpass_filter(self, data: np.ndarray, lowcut=0.5, highcut=40.0) -> np.ndarray:
        """Apply Butterworth bandpass filter."""
        nyquist = 0.5 * self.sampling_rate
        low = lowcut / nyquist
        high = highcut / nyquist
        # Check if high is valid (must be < 1.0)
        if high >= 1.0:
            high = 0.99
            
        b, a = signal.butter(1, [low, high], btype='band')
        return signal.filtfilt(b, a, data, axis=-1)
        
    def apply_notch_filter(self, data: np.ndarray, f0=50.0, Q=30.0) -> np.ndarray:
        """Apply notch filter to remove powerline noise (50/60Hz)."""
        nyquist = 0.5 * self.sampling_rate
        if f0 >= nyquist:
            return data # Cannot filter frequencies above nyquist
        w0 = f0 / nyquist
        b, a = signal.iirnotch(w0, Q)
        return signal.filtfilt(b, a, data, axis=-1)

    def fit_scaler(self, train_data: np.ndarray):
        """Fit the scaler strictly on training data to prevent data leakage."""
        # Reshape to 2D for scaler if it's 3D (samples, window, channels)
        if len(train_data.shape) == 3:
            samples, window, channels = train_data.shape
            reshaped = train_data.reshape(-1, channels)
            self.scaler.fit(reshaped)
        elif len(train_data.shape) == 2:
            self.scaler.fit(train_data)
        else:
            self.scaler.fit(train_data.reshape(-1, 1))
        self.is_fitted = True

    def transform(self, data: np.ndarray) -> np.ndarray:
        """Transform data using the pre-fitted scaler."""
        if not self.is_fitted:
            raise ValueError("Scaler has not been fitted. Call fit_scaler() on training data first.")
            
        original_shape = data.shape
        if len(data.shape) == 3:
            samples, window, channels = data.shape
            reshaped = data.reshape(-1, channels)
            transformed = self.scaler.transform(reshaped)
            return transformed.reshape(original_shape)
        elif len(data.shape) == 2:
            return self.scaler.transform(data)
        else:
            transformed = self.scaler.transform(data.reshape(-1, 1))
            return transformed.flatten()

    def process_training_data(self, X_train: np.ndarray) -> np.ndarray:
        """Process training data and fit the scaler."""
        X_clean = self.handle_missing_values(X_train)
        X_filtered = self.apply_bandpass_filter(X_clean)
        X_filtered = self.apply_notch_filter(X_filtered)
        self.fit_scaler(X_filtered)
        X_normalized = self.transform(X_filtered)
        return X_normalized

    def process_inference_data(self, X_test: np.ndarray) -> np.ndarray:
        """Process test/inference data using the pre-fitted pipeline."""
        X_clean = self.handle_missing_values(X_test)
        X_filtered = self.apply_bandpass_filter(X_clean)
        X_filtered = self.apply_notch_filter(X_filtered)
        X_normalized = self.transform(X_filtered)
        return X_normalized

    def extract_trend_features(self, hr_sequence, hrv_sequence):
        """For the trend-based pathway (when ECG is missing)"""
        return {
            "mean_hr": np.mean(hr_sequence),
            "std_hr": np.std(hr_sequence),
            "mean_hrv": np.mean(hrv_sequence)
        }

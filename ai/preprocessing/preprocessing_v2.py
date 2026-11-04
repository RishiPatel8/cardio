import numpy as np
import scipy.signal
import joblib
from sklearn.preprocessing import StandardScaler

class PreprocessingPipelineV2:
    def __init__(self, sampling_rate=100, window_size=1000):
        self.sampling_rate = sampling_rate
        self.window_size = window_size
        self.scaler = StandardScaler()
        self.is_fitted = False

    def bandpass_filter(self, signal, lowcut=0.5, highcut=45.0, order=3):
        """
        Apply a bandpass filter to remove baseline wander and high-frequency noise.
        """
        nyquist = 0.5 * self.sampling_rate
        low = lowcut / nyquist
        high = highcut / nyquist
        # Ensure high is strictly less than 1.0 (Nyquist)
        if high >= 1.0:
            high = 0.99
            
        b, a = scipy.signal.butter(order, [low, high], btype='band')
        filtered_signal = scipy.signal.filtfilt(b, a, signal)
        return filtered_signal
        
    def _apply_filter_to_batch(self, X):
        X_filtered = np.zeros_like(X)
        for i in range(len(X)):
            X_filtered[i] = self.bandpass_filter(X[i])
        return X_filtered

    def fit(self, X_train):
        print("Filtering training data to compute scaler statistics...")
        X_filtered = self._apply_filter_to_batch(X_train)
        print("Fitting StandardScaler...")
        self.scaler.fit(X_filtered)
        self.is_fitted = True

    def transform(self, X):
        if not self.is_fitted:
            raise ValueError("Pipeline not fitted yet. Call fit() on training data first.")
            
        X_filtered = self._apply_filter_to_batch(X)
        X_scaled = self.scaler.transform(X_filtered)
        return X_scaled
        
    def process_training_data(self, X_train):
        self.fit(X_train)
        return self.transform(X_train)
        
    def process_inference_data(self, X_infer):
        return self.transform(X_infer)

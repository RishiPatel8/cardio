import numpy as np
import scipy.signal as signal
from sklearn.preprocessing import StandardScaler
import joblib

class PreprocessingPipelineV6:
    def __init__(self, target_fs=100.0, apply_filter=True):
        self.target_fs = target_fs
        self.apply_filter = apply_filter
        self.scaler = StandardScaler()
        self.is_fitted = False
        
    def _resample(self, waveform, original_fs):
        if original_fs == self.target_fs:
            return waveform
            
        num_samples = int(len(waveform) * self.target_fs / original_fs)
        # Using scipy.signal.resample which applies fourier method (handles anti-aliasing)
        resampled = signal.resample(waveform, num_samples)
        return resampled
        
    def _bandpass_filter(self, waveform, fs):
        lowcut = 0.5
        highcut = 40.0
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        
        # 3rd order Butterworth
        b, a = signal.butter(3, [low, high], btype='band')
        filtered = signal.filtfilt(b, a, waveform)
        return filtered

    def process_inference_data(self, waveforms, original_fs=100.0):
        """
        Process incoming inference data. Waveforms expected as list or 2D array (N_samples, length).
        Returns scaled array (N_samples, target_length)
        """
        processed = []
        for w in waveforms:
            # Bandpass BEFORE resample for better numerical stability on raw high-freq noise
            if self.apply_filter:
                w_filtered = self._bandpass_filter(w, original_fs)
            else:
                w_filtered = w
                
            w_resampled = self._resample(w_filtered, original_fs)
            processed.append(w_resampled)
            
        processed_arr = np.array(processed)
        
        if self.is_fitted:
            # Standard Scaler expects 2D array (samples, features)
            return self.scaler.transform(processed_arr)
        return processed_arr

    def fit_transform(self, waveforms, original_fs=100.0):
        processed = []
        for w in waveforms:
            if self.apply_filter:
                w_filtered = self._bandpass_filter(w, original_fs)
            else:
                w_filtered = w
                
            w_resampled = self._resample(w_filtered, original_fs)
            processed.append(w_resampled)
            
        processed_arr = np.array(processed)
        transformed = self.scaler.fit_transform(processed_arr)
        self.is_fitted = True
        return transformed
        
    def save(self, filepath):
        joblib.dump(self.scaler, filepath)
        
    def load(self, filepath):
        self.scaler = joblib.load(filepath)
        self.is_fitted = True

# V6 4-Class Mapping
def assign_class_v6(scp_codes):
    """
    0 = Normal (NORM)
    1 = AFIB (Atrial Fibrillation)
    2 = Conduction Block (LAFB, LBBB, RBBB, CRBBB, IRBBB, 1AVB, 2AVB, 3AVB)
    3 = Other Arrhythmia
    """
    if 'NORM' in scp_codes:
        return 0
    if 'AFIB' in scp_codes:
        return 1
    
    blocks = ['LAFB', 'LPFB', 'LBBB', 'RBBB', 'CRBBB', 'IRBBB', '1AVB', '2AVB', '3AVB', 'WPW', 'IVCD']
    if any(b in scp_codes for b in blocks):
        return 2
        
    return 3

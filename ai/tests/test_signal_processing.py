import unittest
import numpy as np
from ai.preprocessing.filters import apply_bandpass_filter, normalize_signal, interpolate_missing_samples
from ai.preprocessing.qrs_detection import detect_r_peaks, calculate_rr_intervals

class TestSignalProcessing(unittest.TestCase):
    def setUp(self):
        # Generate 10 seconds of mock ECG lead-II signal (fs = 250 Hz)
        self.fs = 250.0
        self.t = np.arange(0, 10.0, 1.0 / self.fs)
        
        # Generate baseline sinus rhythm carrier wave at 1.2 Hz (approx 72 bpm)
        self.sinus_wave = np.sin(2 * np.pi * 1.2 * self.t)
        
        # Add high-frequency noise and baseline wander
        self.noise = np.sin(2 * np.pi * 50.0 * self.t) * 0.1 # 50Hz powerline interference
        self.wander = np.sin(2 * np.pi * 0.15 * self.t) * 0.5 # baseline sway
        
        self.dirty_signal = self.sinus_wave + self.noise + self.wander

    def test_butterworth_bandpass_attenuation(self):
        """Verifies that the bandpass filter isolates target cardiac frequency bands."""
        filtered = apply_bandpass_filter(self.dirty_signal, lowcut=0.5, highcut=45.0, fs=self.fs)
        self.assertEqual(len(filtered), len(self.dirty_signal))
        
        # Power of high-frequency noise (50Hz) should be attenuated significantly
        fft_dirty = np.abs(np.fft.rfft(self.dirty_signal))
        fft_filtered = np.abs(np.fft.rfft(filtered))
        
        idx_50hz = int(50.0 * 10.0) # frequency bucket index
        self.assertLess(fft_filtered[idx_50hz], fft_dirty[idx_50hz] * 0.05)

    def test_signal_normalization_bounds(self):
        """Validates standard min-max and Z-score scaling parameters."""
        # Minmax normalization bounds test
        normalized_minmax = normalize_signal(self.dirty_signal, method="minmax")
        self.assertAlmostEqual(float(np.min(normalized_minmax)), 0.0)
        self.assertAlmostEqual(float(np.max(normalized_minmax)), 1.0)
        
        # Z-score normalization mean/std verification
        normalized_zscore = normalize_signal(self.dirty_signal, method="zscore")
        self.assertAlmostEqual(float(np.mean(normalized_zscore)), 0.0, places=4)
        self.assertAlmostEqual(float(np.std(normalized_zscore)), 1.0, places=4)

    def test_missing_samples_interpolation(self):
        """Verifies linear interpolation fixes missing NaN sample records."""
        damaged_signal = self.dirty_signal.copy()
        damaged_signal[100:110] = np.nan # inject NaN block
        
        reconstructed = interpolate_missing_samples(damaged_signal)
        self.assertFalse(np.any(np.isnan(reconstructed)))
        self.assertAlmostEqual(float(reconstructed[105]), float((self.dirty_signal[99] + self.dirty_signal[111]) / 2.0), places=1)

    def test_r_peaks_and_rr_intervals(self):
        """Validates peak tracking and difference calculations."""
        # Construct synthetic pulse points matching a sinus rhythm of 72 bpm
        synthetic_ecg = np.zeros(int(self.fs * 5))
        peaks_injected = [250, 458, 666, 874, 1082] # 5 pulses every ~208 samples
        for p in peaks_injected:
            # Inject QRS complex shape
            synthetic_ecg[p-5:p+5] = [0.1, 0.3, 0.6, 1.2, 2.0, 1.5, 0.5, -0.2, -0.1, 0.0]
            
        detected = detect_r_peaks(synthetic_ecg, fs=self.fs)
        # Should detect exactly the 5 injected peak coordinates
        self.assertEqual(len(detected), 5)
        
        intervals = calculate_rr_intervals(detected, fs=self.fs)
        # Verify interval count is N-1
        self.assertEqual(len(intervals), 4)
        # Verify interval represents ~832ms (208 samples / 250 fs)
        self.assertAlmostEqual(float(intervals[0]), 832.0, places=0)

if __name__ == '__main__':
    unittest.main()

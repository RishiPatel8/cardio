from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
import numpy as np

class AISignalPreprocessor(ABC):
    """
    Interface for noise filtering, baseline wander removal, 
    and amplitude normalization of raw ECG/PPG timeseries signals.
    """
    @abstractmethod
    def remove_noise(self, raw_signal: np.ndarray, sampling_rate: int) -> np.ndarray:
        """Filter high-frequency powerline interference and baseline wander."""
        pass

    @abstractmethod
    def normalize_signal(self, signal: np.ndarray) -> np.ndarray:
        """Apply min-max or z-score normalization on the signal array."""
        pass


class AIFeatureExtractor(ABC):
    """
    Interface for QRS complex detection and HRV parameter calculations.
    """
    @abstractmethod
    def detect_peaks(self, clean_signal: np.ndarray, sampling_rate: int) -> np.ndarray:
        """Detect QRS R-peaks using localized thresholding or wavelet transform."""
        pass

    @abstractmethod
    def calculate_hrv_metrics(self, rr_intervals_ms: np.ndarray) -> Dict[str, float]:
        """Calculate statistical metrics (SDRR, RMSSD, pNN50) from R-R peaks."""
        pass


class AIPredictionEngine(ABC):
    """
    Interface for TensorFlow Lite edge and cloud model inference.
    """
    @abstractmethod
    def load_model(self, model_path: str) -> Any:
        """Load TFLite interpreter or TensorFlow model weights."""
        pass

    @abstractmethod
    def run_inference(self, feature_vector: np.ndarray) -> Tuple[str, float]:
        """
        Execute deep-learning forward pass.
        Returns:
            Tuple of (classification_label, confidence_score)
        """
        pass


class AIExplainabilityEngine(ABC):
    """
    Interface for explainable AI outputs (XAI) and clinical diagnostic rationale.
    """
    @abstractmethod
    def generate_shap_values(self, input_data: np.ndarray) -> np.ndarray:
        """Calculate feature importances (e.g. SHAP or Integrated Gradients)."""
        pass

    @abstractmethod
    def compile_clinical_insights(self, classification: str, confidence: float, hrv_metrics: Dict[str, float]) -> List[str]:
        """Compile natural language justifications for medical professionals."""
        pass

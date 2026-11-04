import os
import numpy as np
from loguru import logger
from ai.explainability.shap_explainer import SHAPExplainer, generate_mock_explanation
from app.core.config import settings

class ShapService:
    def __init__(self, model_path: str, bg_path: str):
        self.explainer = None
        self.mode = getattr(settings, "PREDICTION_MODE", os.environ.get("PREDICTION_MODE", "demo")).lower()
        
        if self.mode == "real":
            if os.path.exists(bg_path):
                real_bg = np.load(bg_path)
                try:
                    self.explainer = SHAPExplainer(model_path, real_bg)
                    logger.info(f"Real SHAP explainer loaded successfully with background from {bg_path}")
                except Exception as e:
                    logger.error(f"Failed to initialize real SHAP explainer: {e}")
            else:
                logger.error(f"SHAP background not found at {bg_path}. SHAP requires valid background.")
                
    def get_explanation(self, waveform_data: np.ndarray, target_class: int = None):
        if self.mode == "real":
            if self.explainer:
                try:
                    return self.explainer.explain(waveform_data, target_class=target_class)
                except Exception as e:
                    logger.error(f"SHAP calculation failed: {e}")
                    raise Exception("SHAP explanation failed")
            else:
                raise Exception("SHAP explainer not initialized.")
        if self.mode == "demo" or self.explainer is None:
            if os.environ.get("PREDICTION_MODE", "demo").lower() == "real":
                raise Exception("Mock SHAP explanations explicitly blocked in real mode")
            return generate_mock_explanation()

shap_service_instance = None

def get_shap_service(model_path: str, bg_path: str) -> ShapService:
    global shap_service_instance
    if shap_service_instance is None:
        shap_service_instance = ShapService(model_path, bg_path)
    return shap_service_instance

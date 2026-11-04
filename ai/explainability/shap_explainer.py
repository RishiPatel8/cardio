import shap
import numpy as np
import logging

try:
    import tensorflow as tf
except ImportError:
    tf = None
    logging.warning("Tensorflow not available, SHAPExplainer will fail if instantiated.")

class SHAPExplainer:
    def __init__(self, model_path: str, background_data: np.ndarray):
        """
        model_path: path to the saved model (.h5 or .pkl)
        background_data: A representative sample of the training data
        """
        self.is_sklearn = model_path.endswith(".pkl")
        
        if self.is_sklearn:
            import joblib
            self.model = joblib.load(model_path)
            self.input_shape = (187,)
            # For tree models, we don't necessarily need background data for TreeExplainer
            # but we can use it to get expected values.
            self.explainer = shap.TreeExplainer(self.model)
        else:
            if tf is None:
                raise RuntimeError("TensorFlow is required for Keras SHAPExplainer but is not available.")
            self.model = tf.keras.models.load_model(model_path, compile=False)
            
            # Flatten background data for KernelExplainer since it expects 2D for Keras models usually,
            # but we can wrap the model prediction to handle 3D internally.
            self.input_shape = background_data.shape[1:]
            
            # Summarize background data to K=10 to keep KernelExplainer computationally feasible
            background_summary = shap.sample(background_data.reshape(background_data.shape[0], -1), 10)
            
            def predict_fn(x):
                # x is shape (samples, 1000)
                x_reshaped = x.reshape((x.shape[0], *self.input_shape))
                preds = self.model.predict(x_reshaped, verbose=0)
                return preds
                
            self.explainer = shap.KernelExplainer(predict_fn, background_summary)

    def explain(self, sample: np.ndarray, feature_names: list = None, target_class: int = None):
        """
        Explain a single prediction.
        sample: shape (1, time_steps) or (1, time_steps, channels)
        """
        if self.is_sklearn:
            sample_flat = sample.reshape((1, -1))
            shap_values = self.explainer.shap_values(sample_flat)
            # TreeExplainer for binary classification might return a list [class0, class1] or just class1 depending on implementation
            if isinstance(shap_values, list):
                agg_shap = np.abs(shap_values[1][0])
            else:
                # If single array returned (common for regression or some binary RF implementations)
                if len(shap_values.shape) == 3: # (samples, features, classes)
                    agg_shap = np.abs(shap_values[0, :, target_class if target_class is not None else 1])
                else:
                    agg_shap = np.abs(shap_values[0])
        else:
            sample_flat = sample.reshape((1, -1))
            # KernelExplainer is slow, so we only explain the given sample. Use nsamples > features (1000)
            shap_values = self.explainer.shap_values(sample_flat, nsamples=1200)
            
            if isinstance(shap_values, list):
                target = target_class if target_class is not None else 1
                agg_shap = np.abs(shap_values[target][0])
            else:
                if len(shap_values.shape) == 3:
                    target = target_class if target_class is not None else 1
                    agg_shap = np.abs(shap_values[0, :, target])
                else:
                    agg_shap = np.abs(shap_values[0])
        
        contributions = []
        if feature_names is None:
            # We want to format the features correctly based on the temporal mapping requirements
            feature_names = [f"time_{i}" for i in range(len(agg_shap))]
            
        for i, name in enumerate(feature_names):
            if i < len(agg_shap):
                contributions.append({
                    "feature": name,
                    "contribution": float(agg_shap[i])
                })
            
        # Sort by contribution magnitude
        contributions = sorted(contributions, key=lambda x: x["contribution"], reverse=True)
        return contributions

def generate_mock_explanation():
    """Fallback when model is not fully trained or in DEMO mode."""
    return [
        {"feature": "Heart Rate Trend", "contribution": 0.45},
        {"feature": "HRV (RMSSD)", "contribution": 0.30},
        {"feature": "Sleep Pattern", "contribution": 0.15},
        {"feature": "Activity Level", "contribution": 0.10}
    ]

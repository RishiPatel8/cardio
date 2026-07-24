import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from typing import Dict, Any, Tuple

# Try importing XGBoost safely for environments with package availability
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

class RiskClassifierEnsemble:
    def __init__(self):
        self.rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.lr_model = LogisticRegression(max_iter=1000, random_state=42)
        if XGB_AVAILABLE:
            self.xgb_model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
        else:
            self.xgb_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
            
        self.best_model_name = "random_forest"
        self.best_model = self.rf_model

    def train_and_evaluate(
        self, 
        X_train: np.ndarray, 
        y_train: np.ndarray, 
        X_val: np.ndarray, 
        y_val: np.ndarray
    ) -> Dict[str, Any]:
        """Trains multiple classifiers, evaluates validation metrics, and auto-selects the best estimator."""
        models = {
            "random_forest": self.rf_model,
            "logistic_regression": self.lr_model,
            "gradient_boosting": self.xgb_model
        }
        
        benchmarks = {}
        for name, model in models.items():
            # Fit model
            model.fit(X_train, y_train)
            
            # Predict
            preds = model.predict(X_val)
            probs = model.predict_proba(X_val)[:, 1] if hasattr(model, "predict_proba") else preds
            
            # Metrics
            acc = accuracy_score(y_val, preds)
            f1 = f1_score(y_val, preds, average='binary')
            try:
                auc = roc_auc_score(y_val, probs)
            except Exception:
                auc = acc
                
            benchmarks[name] = {
                "accuracy": float(acc),
                "f1_score": float(f1),
                "roc_auc": float(auc)
            }
            
        # Select best model based on F1-score
        best_name = max(benchmarks, key=lambda k: benchmarks[k]["f1_score"])
        self.best_model_name = best_name
        self.best_model = models[best_name]
        
        return {
            "benchmarks": benchmarks,
            "best_model_selected": best_name,
            "best_metrics": benchmarks[best_name]
        }

    def predict_risk(self, X: np.ndarray) -> Tuple[int, float, float]:
        """Returns (prediction_class, probability_score, confidence_score) using the best-performing model."""
        prediction = int(self.best_model.predict(X)[0])
        probabilities = self.best_model.predict_proba(X)[0] if hasattr(self.best_model, "predict_proba") else [0.0, 1.0]
        
        prob_risk = float(probabilities[1])
        # Confidence score represents the model's confidence in its chosen class
        confidence = float(np.max(probabilities)) * 100.0
        
        return prediction, prob_risk, confidence

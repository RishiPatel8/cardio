import os
import json
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import logging

try:
    from imblearn.over_sampling import SMOTE
except ImportError:
    SMOTE = None

from ai.preprocessing.pipeline import PreprocessingPipeline
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def train_and_evaluate():
    logger.info("Loading patient-isolated splits...")
    try:
        X_train_raw = np.load("ai/data/splits/X_train.npy")
        y_train = np.load("ai/data/splits/y_train.npy")
        X_val_raw = np.load("ai/data/splits/X_val.npy")
        y_val = np.load("ai/data/splits/y_val.npy")
        X_test_raw = np.load("ai/data/splits/X_test.npy")
        y_test = np.load("ai/data/splits/y_test.npy")
    except Exception as e:
        logger.error(f"Failed to load splits: {e}")
        return

    logger.info("Fitting authoritative Preprocessing pipeline ONLY on training data...")
    pipeline = PreprocessingPipeline()
    X_train_scaled = pipeline.process_training_data(X_train_raw)
    X_val_scaled = pipeline.process_inference_data(X_val_raw)
    X_test_scaled = pipeline.process_inference_data(X_test_raw)
    
    # Flatten for ML models (187, 1) -> (187,)
    X_train = X_train_scaled.reshape(X_train_scaled.shape[0], -1)
    X_val = X_val_scaled.reshape(X_val_scaled.shape[0], -1)
    X_test = X_test_scaled.reshape(X_test_scaled.shape[0], -1)
    
    # Save the fitted pipeline
    import joblib
    os.makedirs("ai/artifacts/models", exist_ok=True)
    joblib.dump(pipeline, "ai/artifacts/models/preprocessing_pipeline.pkl")
    
    # Map multi-class to binary for CardioGuard (0: Normal, 1-4: Abnormal -> 1)
    y_train_bin = (y_train > 0).astype(int)
    y_val_bin = (y_val > 0).astype(int)
    y_test_bin = (y_test > 0).astype(int)

    if SMOTE is not None:
        logger.info("Applying SMOTE to training partition ONLY...")
        smote = SMOTE(random_state=42)
        X_train_res, y_train_res = smote.fit_resample(X_train, y_train_bin)
    else:
        logger.warning("SMOTE is blocked. Proceeding with imbalanced training.")
        X_train_res, y_train_res = X_train, y_train_bin

    models = {
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
        "Decision Tree": DecisionTreeClassifier(random_state=42)
    }

    results = {}
    
    os.makedirs("ai/artifacts/models", exist_ok=True)
    
    logger.info("Training classical ML models on patient-isolated WFDB dataset...")
    for name, model in models.items():
        logger.info(f"Training {name}...")
        model.fit(X_train_res, y_train_res)
        # Save model
        import joblib
        model_path = f"ai/artifacts/models/{name.replace(' ', '_').lower()}.pkl"
        joblib.dump(model, model_path)
        
        logger.info(f"Evaluating {name} on untouched TEST partition...")
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred
        
        acc = accuracy_score(y_test_bin, y_pred)
        prec = precision_score(y_test_bin, y_pred, zero_division=0)
        rec = recall_score(y_test_bin, y_pred, zero_division=0)
        f1 = f1_score(y_test_bin, y_pred, zero_division=0)
        auc = roc_auc_score(y_test_bin, y_prob)
        tn, fp, fn, tp = confusion_matrix(y_test_bin, y_pred).ravel()
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0
        
        results[name] = {
            "Accuracy": acc,
            "Precision": prec,
            "Recall": rec,
            "Specificity": spec,
            "F1": f1,
            "ROC_AUC": auc
        }
        logger.info(f"{name} -> Recall: {rec:.3f}, Specificity: {spec:.3f}, AUC: {auc:.3f}")

    results["CNN+LSTM"] = "BLOCKED: Requires TensorFlow environment which is absent."
    results["CNN"] = "BLOCKED: Requires TensorFlow."
    results["LSTM"] = "BLOCKED: Requires TensorFlow."

    os.makedirs("ai/results", exist_ok=True)
    with open("ai/results/physionet_model_evaluation.json", "w") as f:
        json.dump(results, f, indent=4)
        
    logger.info("Training and evaluation completed successfully.")

if __name__ == "__main__":
    train_and_evaluate()

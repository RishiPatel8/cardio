import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, roc_curve
import matplotlib.pyplot as plt

# Local imports
from ai.config.experiment_config import config
from ai.preprocessing.pipeline import PreprocessingPipeline
from ai.models.baselines import get_svm_model, get_rf_model, get_dt_model

try:
    from ai.models.cnn_lstm import build_cnn_lstm, build_cnn, build_lstm
    TF_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: TensorFlow could not be loaded ({e}). Deep Learning models will be skipped.")
    TF_AVAILABLE = False

def setup_directories():
    dirs = [
        config.BASE_RESULTS_DIR,
        os.path.join(config.BASE_RESULTS_DIR, "baselines"),
        os.path.join(config.BASE_RESULTS_DIR, "confusion_matrices"),
        os.path.join(config.BASE_RESULTS_DIR, "roc_curves"),
        os.path.join(config.BASE_RESULTS_DIR, "training_curves"),
        config.BASE_ARTIFACTS_DIR,
        os.path.join(config.BASE_ARTIFACTS_DIR, "svm"),
        os.path.join(config.BASE_ARTIFACTS_DIR, "random_forest"),
        os.path.join(config.BASE_ARTIFACTS_DIR, "decision_tree"),
        os.path.join(config.BASE_ARTIFACTS_DIR, "cnn"),
        os.path.join(config.BASE_ARTIFACTS_DIR, "lstm"),
        os.path.join(config.BASE_ARTIFACTS_DIR, "cnn_lstm")
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def load_and_split_data(train_path, test_path, subsample_ratio=1.0):
    if not os.path.exists(train_path) or not os.path.exists(test_path):
        raise FileNotFoundError(f"Datasets not found at {train_path} or {test_path}")
        
    print(f"Loading data from {train_path} and {test_path}")
    train_df = pd.read_csv(train_path, header=None)
    test_df = pd.read_csv(test_path, header=None)
    
    if subsample_ratio < 1.0:
        # Stratified subsample
        train_df = train_df.groupby(187, group_keys=False).apply(lambda x: x.sample(frac=subsample_ratio, random_state=config.RANDOM_SEED))
        test_df = test_df.groupby(187, group_keys=False).apply(lambda x: x.sample(frac=subsample_ratio, random_state=config.RANDOM_SEED))
        print(f"Subsampled data to {subsample_ratio*100}%")

    X_train_full = train_df.iloc[:, :-1].values
    y_train_full = train_df.iloc[:, -1].values
    
    X_test = test_df.iloc[:, :-1].values
    y_test = test_df.iloc[:, -1].values
    
    # Binarize labels (0: Normal, 1-4: Abnormal) as requested for AF/Arrhythmia Risk
    y_train_full = np.where(y_train_full > 0, 1, 0)
    y_test = np.where(y_test > 0, 1, 0)
    
    # Split official train into train and validation (stratified)
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full, test_size=0.15, stratify=y_train_full, random_state=config.RANDOM_SEED
    )
    
    return X_train, y_train, X_val, y_val, X_test, y_test

def plot_and_save_confusion_matrix(y_true, y_pred, model_name):
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(6, 5))
    plt.matshow(cm, cmap=plt.cm.Blues, alpha=0.3)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(x=j, y=i, s=cm[i, j], va='center', ha='center')
    plt.xlabel('Predicted label')
    plt.ylabel('True label')
    plt.title(f'Confusion Matrix: {model_name}')
    plt.savefig(os.path.join(config.BASE_RESULTS_DIR, "confusion_matrices", f"{model_name}.png"))
    plt.close('all')
    return cm.tolist()

def plot_and_save_roc_curve(y_true, y_prob, model_name):
    try:
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        auc_score = roc_auc_score(y_true, y_prob)
        plt.figure(figsize=(6, 5))
        plt.plot(fpr, tpr, label=f'AUC = {auc_score:.3f}')
        plt.plot([0, 1], [0, 1], 'k--')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'ROC Curve: {model_name}')
        plt.legend(loc='lower right')
        plt.savefig(os.path.join(config.BASE_RESULTS_DIR, "roc_curves", f"{model_name}.png"))
        plt.close('all')
    except Exception as e:
        print(f"Could not generate ROC for {model_name}: {e}")

def plot_and_save_training_curves(history, model_name):
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    plt.plot(history.history['loss'], label='Train Loss')
    plt.plot(history.history['val_loss'], label='Val Loss')
    plt.legend()
    plt.title(f'{model_name} Loss')
    
    plt.subplot(1, 2, 2)
    plt.plot(history.history['accuracy'], label='Train Acc')
    plt.plot(history.history['val_accuracy'], label='Val Acc')
    plt.legend()
    plt.title(f'{model_name} Accuracy')
    
    plt.savefig(os.path.join(config.BASE_RESULTS_DIR, "training_curves", f"{model_name}.png"))
    plt.close('all')

def evaluate_model(model, X_test, y_test, model_name, is_keras=False):
    if is_keras:
        y_prob = model.predict(X_test, verbose=0).flatten()
        y_pred = (y_prob > 0.5).astype(int)
    else:
        y_pred = model.predict(X_test)
        if hasattr(model, "predict_proba"):
            y_prob = model.predict_proba(X_test)[:, 1]
        else:
            y_prob = y_pred

    metrics = {
        "Accuracy": float(accuracy_score(y_test, y_pred)),
        "Precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "Recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "F1": float(f1_score(y_test, y_pred, zero_division=0)),
        "AUC": float(roc_auc_score(y_test, y_prob)) if len(np.unique(y_test)) > 1 else 0.0
    }
    
    cm = plot_and_save_confusion_matrix(y_test, y_pred, model_name)
    plot_and_save_roc_curve(y_test, y_prob, model_name)
    
    result_path = os.path.join(config.BASE_RESULTS_DIR, "baselines", f"{model_name.replace(' ', '_').lower()}.json")
    with open(result_path, "w") as f:
        json.dump({"metrics": metrics, "confusion_matrix": cm}, f, indent=4)
        
    return metrics

def save_model_metadata(model_name, metrics):
    metadata = {
        "model_version": f"{model_name.lower()}-v1.0",
        "experiment_id": config.EXPERIMENT_ID,
        "dataset": "MIT-BIH Arrhythmia Database",
        "dataset_source": "Kaggle shayanfazeli/heartbeat",
        "classification_task": config.CLASSIFICATION_TASK,
        "input_shape": [config.WINDOW_SIZE, 1],
        "preprocessing_version": "v1.0",
        "metrics": metrics
    }
    path = os.path.join(config.BASE_ARTIFACTS_DIR, model_name.lower(), "metadata.json")
    with open(path, "w") as f:
        json.dump(metadata, f, indent=4)

def run_experiment():
    print(f"Starting {config.EXPERIMENT_ID}")
    setup_directories()
    
    # 1. Load Data
    try:
        X_train, y_train, X_val, y_val, X_test, y_test = load_and_split_data(
            config.DATASET_PATH_TRAIN, 
            config.DATASET_PATH_TEST, 
            subsample_ratio=config.SUBSAMPLE_RATIO
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    # 2. Preprocessing (Strictly fit on X_train ONLY to prevent data leakage)
    print("Preprocessing data...")
    pipeline = PreprocessingPipeline(sampling_rate=config.SAMPLING_RATE, window_size=config.WINDOW_SIZE)
    X_train_processed = pipeline.process_training_data(X_train)
    X_val_processed = pipeline.process_inference_data(X_val)
    X_test_processed = pipeline.process_inference_data(X_test)
    
    import joblib
    joblib.dump(pipeline.scaler, os.path.join(config.BASE_ARTIFACTS_DIR, "scaler.pkl"))
    
    # 3. SMOTE (Training only!)
    print("Applying SMOTE to training data only...")
    smote = SMOTE(random_state=config.RANDOM_SEED)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train_processed, y_train)
    
    all_metrics = {}

    # 4. Train Baselines
    models = {
        "SVM": get_svm_model(),
        "Random Forest": get_rf_model(),
        "Decision Tree": get_dt_model()
    }
    
    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(X_train_resampled, y_train_resampled)
        metrics = evaluate_model(model, X_test_processed, y_test, name)
        all_metrics[name] = metrics
        
        # Save model
        joblib.dump(model, os.path.join(config.BASE_ARTIFACTS_DIR, name.replace(" ", "_").lower(), "model.pkl"))
        save_model_metadata(name.replace(" ", "_"), metrics)
        
    # 5. Train Deep Learning Models
    if TF_AVAILABLE:
        print("Training Deep Learning Models...")
        # Reshape for Conv1D/LSTM: (samples, time_steps, features)
        X_train_dl = X_train_resampled.reshape((X_train_resampled.shape[0], X_train_resampled.shape[1], 1))
        X_val_dl = X_val_processed.reshape((X_val_processed.shape[0], X_val_processed.shape[1], 1))
        X_test_dl = X_test_processed.reshape((X_test_processed.shape[0], X_test_processed.shape[1], 1))
        
        dl_configs = {
            "CNN": build_cnn(input_shape=(config.WINDOW_SIZE, 1), num_classes=1),
            "LSTM": build_lstm(input_shape=(config.WINDOW_SIZE, 1), num_classes=1),
            "CNN_LSTM": build_cnn_lstm(input_shape=(config.WINDOW_SIZE, 1), num_classes=1)
        }
        
        for dl_name, dl_model in dl_configs.items():
            print(f"Training {dl_name}...")
            history = dl_model.fit(
                X_train_dl, y_train_resampled, 
                epochs=config.EPOCHS, 
                batch_size=config.BATCH_SIZE, 
                validation_data=(X_val_dl, y_val),
                verbose=1
            )
            
            plot_and_save_training_curves(history, dl_name)
            
            metrics = evaluate_model(dl_model, X_test_dl, y_test, dl_name, is_keras=True)
            all_metrics[dl_name] = metrics
            
            # Save DL model artifact
            model_path = os.path.join(config.BASE_ARTIFACTS_DIR, dl_name.lower(), f"{dl_name.lower()}.h5")
            dl_model.save(model_path)
            save_model_metadata(dl_name, metrics)
            print(f"{dl_name} model saved to {model_path}")
        
        # Save active model symlink/copy for the API
        import shutil
        shutil.copyfile(
            os.path.join(config.BASE_ARTIFACTS_DIR, "cnn_lstm", "cnn_lstm.h5"), 
            os.path.join(os.path.dirname(config.BASE_ARTIFACTS_DIR), "cnn_lstm.h5")
        )
    else:
        print("Skipping Deep Learning training due to TensorFlow load failure.")
        all_metrics["CNN"] = "FAILED"
        all_metrics["LSTM"] = "FAILED"
        all_metrics["CNN_LSTM"] = "FAILED"
    
    # 6. Save Comparison
    comparison_path = os.path.join(config.BASE_RESULTS_DIR, "comparison.json")
    with open(comparison_path, "w") as f:
        json.dump(all_metrics, f, indent=4)
        
    df = pd.DataFrame(all_metrics).T
    df.to_csv(os.path.join(config.BASE_RESULTS_DIR, "comparison.csv"))
    print("Experiment complete. Metrics saved.")

if __name__ == "__main__":
    np.random.seed(config.RANDOM_SEED)
    import tensorflow as tf
    tf.random.set_seed(config.RANDOM_SEED)
    run_experiment()

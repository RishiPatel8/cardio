import os
import sys
import numpy as np
import tensorflow as tf
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
import joblib
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ai.preprocessing.pipeline import PreprocessingPipeline
from ai.models.cnn_lstm import build_cnn_lstm

def get_class_weights(y_train):
    classes = np.unique(y_train)
    weights = compute_class_weight('balanced', classes=classes, y=y_train)
    return dict(zip(classes, weights))

def evaluate_and_save_report(y_true, y_pred, y_prob, output_dir):
    report = classification_report(y_true, y_pred, target_names=["NORM", "AFIB", "OTHER"], output_dict=True)
    cm = confusion_matrix(y_true, y_pred)
    
    with open(os.path.join(output_dir, "classification_report.json"), "w") as f:
        json.dump(report, f, indent=4)
        
    print("Classification Report:")
    print(classification_report(y_true, y_pred, target_names=["NORM", "AFIB", "OTHER"]))
    print("Confusion Matrix:")
    print(cm)
    
    with open(os.path.join(output_dir, "metrics.txt"), "w") as f:
        f.write("Classification Report:\n")
        f.write(classification_report(y_true, y_pred, target_names=["NORM", "AFIB", "OTHER"]))
        f.write("\nConfusion Matrix:\n")
        f.write(np.array2string(cm, separator=', '))

def train():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'processed_ptbxl'))
    artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'models', 'cnn_lstm_v2'))
    os.makedirs(artifacts_dir, exist_ok=True)
    
    print("Loading PTB-XL processed arrays...")
    X = np.load(os.path.join(data_dir, 'X.npy'))
    y = np.load(os.path.join(data_dir, 'y.npy'))
    folds = np.load(os.path.join(data_dir, 'folds.npy'))
    
    # Train: Folds 1-8, Val: Fold 9, Test: Fold 10
    train_mask = folds <= 8
    val_mask = folds == 9
    test_mask = folds == 10
    
    # If the sampled dataset didn't happen to sample enough for fold 9/10, fall back to basic split
    if np.sum(val_mask) == 0 or np.sum(test_mask) == 0:
        print("Warning: Fold 9 or 10 is empty (likely due to heavy subsampling). Using a random split instead.")
        from sklearn.model_selection import train_test_split
        X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.1, stratify=y, random_state=42)
        X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.1, stratify=y_temp, random_state=42)
    else:
        X_train, y_train = X[train_mask], y[train_mask]
        X_val, y_val = X[val_mask], y[val_mask]
        X_test, y_test = X[test_mask], y[test_mask]
        
    print(f"Train size: {len(X_train)}, Val size: {len(X_val)}, Test size: {len(X_test)}")
    
    print("Preprocessing data (1000 samples, 100Hz)...")
    pipeline = PreprocessingPipeline(sampling_rate=100, window_size=1000)
    X_train_processed = pipeline.process_training_data(X_train)
    X_val_processed = pipeline.process_inference_data(X_val)
    X_test_processed = pipeline.process_inference_data(X_test)
    
    # Reshape for CNN
    X_train_processed = X_train_processed.reshape(-1, 1000, 1)
    X_val_processed = X_val_processed.reshape(-1, 1000, 1)
    X_test_processed = X_test_processed.reshape(-1, 1000, 1)
    
    print("Saving scaler artifact...")
    joblib.dump(pipeline.scaler, os.path.join(artifacts_dir, 'scaler.pkl'))
    
    print("Saving SHAP background dataset (100 samples)...")
    bg_samples = min(100, len(X_train_processed))
    np.save(os.path.join(artifacts_dir, 'X_train_background.npy'), X_train_processed[:bg_samples])
    
    print("Building model...")
    model = build_cnn_lstm(input_shape=(1000, 1), num_classes=3)
    model.summary()
    
    class_weights = get_class_weights(y_train)
    print(f"Class Weights: {class_weights}")
    
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
        tf.keras.callbacks.ModelCheckpoint(os.path.join(artifacts_dir, 'cnn_lstm_v2.h5'), save_best_only=True)
    ]
    
    print("Training...")
    history = model.fit(
        X_train_processed, y_train,
        validation_data=(X_val_processed, y_val),
        epochs=30,
        batch_size=32,
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=1
    )
    
    print("Evaluating on held-out test set...")
    # Load best model
    model = tf.keras.models.load_model(os.path.join(artifacts_dir, 'cnn_lstm_v2.h5'))
    
    y_prob = model.predict(X_test_processed)
    y_pred = np.argmax(y_prob, axis=1)
    
    evaluate_and_save_report(y_test, y_pred, y_prob, artifacts_dir)
    print("Done! Model saved to artifacts/models/cnn_lstm_v2")

if __name__ == "__main__":
    train()

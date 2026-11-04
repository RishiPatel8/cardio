import os
import sys
import numpy as np
import tensorflow as tf
from sklearn.utils.class_weight import compute_class_weight
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ai.preprocessing.preprocessing_v3 import PreprocessingPipelineV3
from ai.training.experiments import build_1d_cnn, build_cnn_lstm, build_cnn_bilstm

# Reproducibility
tf.random.set_seed(42)
np.random.seed(42)

def augment_ecg_tf(x, y):
    """TF-native data augmentation mapping function for tf.data.Dataset."""
    x = tf.cast(x, tf.float32)
    # 50% chance to add noise
    if tf.random.uniform([]) > 0.5:
        noise = tf.random.normal(shape=tf.shape(x), mean=0.0, stddev=0.05)
        x = x + noise
    
    # 50% chance to add baseline wander (low freq)
    if tf.random.uniform([]) > 0.5:
        # Simple sinusoidal baseline wander
        t = tf.linspace(0.0, 10.0, 1000)
        t = tf.reshape(t, (1000, 1))
        wander = 0.5 * tf.math.sin(2.0 * 3.14159 * 0.5 * t)
        x = x + tf.cast(wander, tf.float32)
        
    return x, y

def create_dataset(X, y, batch_size=64, augment=False, shuffle=False):
    dataset = tf.data.Dataset.from_tensor_slices((X, y))
    # Cache before augmentation so we don't re-read/preprocess
    dataset = dataset.cache()
    if shuffle:
        dataset = dataset.shuffle(buffer_size=10000)
    if augment:
        dataset = dataset.map(augment_ecg_tf, num_parallel_calls=tf.data.AUTOTUNE)
    dataset = dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return dataset

def train_v4():
    print("Initializing V4 Training...")
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'processed_ptbxl_v3'))
    artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'models', 'v4_full'))
    os.makedirs(artifacts_dir, exist_ok=True)
    
    print("Loading data...")
    X = np.load(os.path.join(data_dir, 'X.npy'))
    y = np.load(os.path.join(data_dir, 'y.npy'))
    folds = np.load(os.path.join(data_dir, 'folds.npy'))
    
    train_mask = folds <= 8
    val_mask = folds == 9
    
    X_train_raw, y_train = X[train_mask], y[train_mask]
    X_val_raw, y_val = X[val_mask], y[val_mask]
    
    print("Applying V4 Preprocessing (reusing V3 pipeline for parity)...")
    pipeline = PreprocessingPipelineV3()
    
    X_train_processed = pipeline.process_training_data(X_train_raw)
    X_val_processed = pipeline.process_inference_data(X_val_raw)
    
    X_train_processed = X_train_processed.reshape(-1, 1000, 1)
    X_val_processed = X_val_processed.reshape(-1, 1000, 1)
    
    pipeline.save(os.path.join(artifacts_dir, 'scaler_v4.pkl'))
    
    # Save SHAP background (100 random samples from training set)
    bg_indices = np.random.choice(len(X_train_processed), 100, replace=False)
    shap_bg = X_train_processed[bg_indices]
    np.save(os.path.join(artifacts_dir, 'shap_background.npy'), shap_bg)
    
    # Class Weights
    classes = np.unique(y_train)
    weights = compute_class_weight('balanced', classes=classes, y=y_train)
    class_weights = dict(zip(classes, weights))
    print(f"Class Weights: {class_weights}")
    
    train_ds = create_dataset(X_train_processed, y_train, batch_size=64, augment=True, shuffle=True)
    val_ds = create_dataset(X_val_processed, y_val, batch_size=64, augment=False, shuffle=False)
    
    models = {
        '1d_cnn': build_1d_cnn(),
        'cnn_bilstm': build_cnn_bilstm()
    }
    
    best_val_loss = float('inf')
    best_model_name = None
    
    for name, model in models.items():
        print(f"\\n--- Training {name} ---")
        callbacks = [
            tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=6, restore_best_weights=True),
            tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3)
        ]
        
        # We save models to their own subdirectories to satisfy Phase 22 Artifact Management
        model_dir = os.path.join(artifacts_dir, name)
        os.makedirs(model_dir, exist_ok=True)
        
        history = model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=25,
            class_weight=class_weights,
            callbacks=callbacks,
            verbose=1
        )
        
        val_loss, val_acc = model.evaluate(val_ds, verbose=0)
        print(f"{name} Validation Loss: {val_loss:.4f}, Accuracy: {val_acc:.4f}")
        
        # Save as both h5 and SavedModel format
        model.save(os.path.join(model_dir, f'{name}.h5'))
        tf.saved_model.save(model, os.path.join(model_dir, 'saved_model'))
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_name = name
            model.save(os.path.join(artifacts_dir, 'best_model.h5'))
            tf.saved_model.save(model, os.path.join(artifacts_dir, 'best_saved_model'))
            
    print(f"\\nBest Architecture Selected: {best_model_name}")
    
    registry = {
        "active_model": best_model_name,
        "artifact_path": os.path.join(artifacts_dir, 'best_model.h5'),
        "preprocessing_artifact": os.path.join(artifacts_dir, 'scaler_v4.pkl'),
        "shap_background_path": os.path.join(artifacts_dir, 'shap_background.npy'),
        "version": "v4-full-run",
        "threshold": 0.5
    }
    
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))
    os.makedirs(config_dir, exist_ok=True)
    with open(os.path.join(config_dir, 'registry.json'), 'w') as f:
        json.dump(registry, f, indent=4)
        
    print("V4 Training Complete. Models saved.")

if __name__ == "__main__":
    train_v4()

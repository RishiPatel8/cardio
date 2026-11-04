import os
import sys
import numpy as np
import tensorflow as tf
from sklearn.utils.class_weight import compute_class_weight
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ai.preprocessing.preprocessing_v3 import PreprocessingPipelineV3
from ai.training.experiments import build_1d_cnn, build_cnn_bilstm, build_resnet, build_tcn

# Reproducibility
tf.random.set_seed(42)
np.random.seed(42)

def augment_ecg_v5(x, y):
    """Advanced Data Augmentation for V5."""
    x = tf.cast(x, tf.float32)
    
    # 30% chance Gaussian noise
    if tf.random.uniform([]) > 0.7:
        x = x + tf.random.normal(shape=tf.shape(x), mean=0.0, stddev=0.03)
        
    # 30% chance baseline wander
    if tf.random.uniform([]) > 0.7:
        t = tf.linspace(0.0, 10.0, 1000)
        t = tf.reshape(t, (1000, 1))
        wander = 0.3 * tf.math.sin(2.0 * 3.14159 * tf.random.uniform([], 0.1, 0.5) * t)
        x = x + tf.cast(wander, tf.float32)
        
    # 20% chance amplitude scaling
    if tf.random.uniform([]) > 0.8:
        scale = tf.random.uniform([], 0.8, 1.2)
        x = x * scale
        
    return x, y

def create_dataset(X, y, batch_size=64, augment=False, shuffle=False):
    dataset = tf.data.Dataset.from_tensor_slices((X, y))
    dataset = dataset.cache()
    if shuffle:
        dataset = dataset.shuffle(buffer_size=10000)
    if augment:
        dataset = dataset.map(augment_ecg_v5, num_parallel_calls=tf.data.AUTOTUNE)
    dataset = dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return dataset

def apply_temperature_scaling(model, val_ds, y_val):
    """
    Fits a Temperature Scaling parameter on the validation set.
    """
    print("Fitting Temperature Scaling on Validation Set...")
    
    # Get raw logits if possible, but our models output softmax.
    # We will hack temperature scaling by taking log of softmax (assuming it didn't clip to exactly 0).
    y_val_pred_probs = model.predict(val_ds, verbose=0)
    # Clip to avoid log(0)
    y_val_pred_probs = np.clip(y_val_pred_probs, 1e-7, 1.0)
    logits = np.log(y_val_pred_probs)
    
    temperature = tf.Variable(initial_value=1.5, trainable=True, dtype=tf.float32)
    
    def compute_loss():
        scaled_logits = logits / temperature
        return tf.reduce_mean(tf.nn.sparse_softmax_cross_entropy_with_logits(
            labels=y_val, logits=scaled_logits))
            
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.01)
    
    for i in range(100):
        with tf.GradientTape() as tape:
            loss = compute_loss()
        grads = tape.gradient(loss, [temperature])
        optimizer.apply_gradients(zip(grads, [temperature]))
        
    final_temp = temperature.numpy()
    print(f"Optimal Temperature found: {final_temp:.3f}")
    return final_temp

def train_v5():
    print("Initializing V5 Training Loop...")
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'processed_ptbxl_v3'))
    artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'models', 'v5_full'))
    os.makedirs(artifacts_dir, exist_ok=True)
    
    print("Loading data...")
    X = np.load(os.path.join(data_dir, 'X.npy'))
    y = np.load(os.path.join(data_dir, 'y.npy'))
    folds = np.load(os.path.join(data_dir, 'folds.npy'))
    patient_ids = np.load(os.path.join(data_dir, 'patient_ids.npy'))
    
    train_mask = folds <= 8
    val_mask = folds == 9
    
    X_train_raw, y_train = X[train_mask], y[train_mask]
    X_val_raw, y_val = X[val_mask], y[val_mask]
    
    print("Applying V5 Preprocessing Pipeline...")
    pipeline = PreprocessingPipelineV3()
    
    X_train_processed = pipeline.process_training_data(X_train_raw)
    X_val_processed = pipeline.process_inference_data(X_val_raw)
    
    X_train_processed = X_train_processed.reshape(-1, 1000, 1)
    X_val_processed = X_val_processed.reshape(-1, 1000, 1)
    
    pipeline.save(os.path.join(artifacts_dir, 'scaler_v5.pkl'))
    
    bg_indices = np.random.choice(len(X_train_processed), 100, replace=False)
    shap_bg = X_train_processed[bg_indices]
    np.save(os.path.join(artifacts_dir, 'shap_background.npy'), shap_bg)
    
    classes = np.unique(y_train)
    weights = compute_class_weight('balanced', classes=classes, y=y_train)
    class_weights = dict(zip(classes, weights))
    
    # Optional: Increase penalty for Class 2 explicitly if it remains weak
    # class_weights[2] = class_weights[2] * 1.5 
    print(f"Class Weights: {class_weights}")
    
    train_ds = create_dataset(X_train_processed, y_train, batch_size=64, augment=True, shuffle=True)
    val_ds = create_dataset(X_val_processed, y_val, batch_size=64, augment=False, shuffle=False)
    
    models = {
        '1d_cnn': build_1d_cnn(),
        'cnn_bilstm': build_cnn_bilstm(),
        'resnet': build_resnet(),
        'tcn': build_tcn()
    }
    
    best_val_loss = float('inf')
    best_model_name = None
    best_model = None
    
    for name, model in models.items():
        print(f"\\n--- Training {name} ---")
        callbacks = [
            tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=6, restore_best_weights=True),
            tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3)
        ]
        
        model_dir = os.path.join(artifacts_dir, name)
        os.makedirs(model_dir, exist_ok=True)
        
        # Train
        model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=25,
            class_weight=class_weights,
            callbacks=callbacks,
            verbose=1
        )
        
        val_loss, val_acc = model.evaluate(val_ds, verbose=0)
        
        # Calculate Macro F1 on Validation
        from sklearn.metrics import f1_score
        y_val_pred = np.argmax(model.predict(val_ds, verbose=0), axis=1)
        macro_f1 = f1_score(y_val, y_val_pred, average='macro')
        
        print(f"{name} Validation Loss: {val_loss:.4f}, Accuracy: {val_acc:.4f}, Macro F1: {macro_f1:.4f}")
        
        model.save(os.path.join(model_dir, f'{name}.h5'))
        
        # Use Macro F1 or Val Loss for selection. We use Val Loss to ensure calibration and general fit.
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_name = name
            best_model = model
            model.save(os.path.join(artifacts_dir, 'best_model.h5'))
            tf.saved_model.save(model, os.path.join(artifacts_dir, 'best_saved_model'))
            
    print(f"\\nBest Architecture Selected: {best_model_name}")
    
    # ----------------------------------------------------
    # PHASE 10: CALIBRATION & THRESHOLD OPTIMIZATION
    # ----------------------------------------------------
    temp = apply_temperature_scaling(best_model, val_ds, y_val)
    
    # Threshold optimization for AFIB
    print("Optimizing AFIB Threshold...")
    y_val_probs = best_model.predict(val_ds, verbose=0)
    y_val_probs = np.clip(y_val_probs, 1e-7, 1.0)
    
    # Apply Temperature Scaling
    logits = np.log(y_val_probs) / temp
    exp_logits = np.exp(logits)
    scaled_probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
    
    best_thresh = 0.5
    best_f1 = 0.0
    for thresh in np.arange(0.2, 0.9, 0.05):
        # Predict 1 if P(AFIB) > thresh AND P(AFIB) > P(Other)
        preds = np.argmax(scaled_probs, axis=1)
        preds[(scaled_probs[:, 1] > thresh) & (scaled_probs[:, 1] > scaled_probs[:, 2])] = 1
        
        f1_1 = f1_score(y_val == 1, preds == 1)
        if f1_1 > best_f1:
            best_f1 = f1_1
            best_thresh = float(thresh)
            
    print(f"Optimal AFIB Threshold: {best_thresh:.3f} (Val F1: {best_f1:.4f})")
    
    registry = {
        "active_model": best_model_name,
        "artifact_path": os.path.join(artifacts_dir, 'best_model.h5'),
        "preprocessing_artifact": os.path.join(artifacts_dir, 'scaler_v5.pkl'),
        "shap_background_path": os.path.join(artifacts_dir, 'shap_background.npy'),
        "version": "v5-full-run",
        "temperature": float(temp),
        "afib_threshold": best_thresh
    }
    
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))
    os.makedirs(config_dir, exist_ok=True)
    with open(os.path.join(config_dir, 'registry.json'), 'w') as f:
        json.dump(registry, f, indent=4)
        
    print("V5 Training Complete.")

if __name__ == "__main__":
    train_v5()

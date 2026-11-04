import os
import sys
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from sklearn.utils.class_weight import compute_class_weight

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ai.training.experiments import ARCHITECTURES

# Reproducibility
np.random.seed(42)
tf.random.set_seed(42)

# --- CONFIGURATION ---
DATA_DIR = os.path.abspath("d:/cardiogaurd/ai/datasets/processed/v7")
ARTIFACT_DIR = os.path.abspath("d:/cardiogaurd/ai/artifacts/models/v7")
EPOCHS = 25
BATCH_SIZE = 64
LR = 0.001
MODELS = ['resnet_improved', 'cnn_lstm', 'tcn', 'transformer']

def get_focal_loss(gamma=2.0, alpha=None):
    """
    Focal Loss for multi-class classification.
    alpha: array of weights for each class
    """
    if alpha is not None:
        alpha = tf.constant(alpha, dtype=tf.float32)
        
    def focal_loss_fixed(y_true, y_pred):
        y_true = tf.cast(y_true, tf.float32)
        epsilon = tf.keras.backend.epsilon()
        y_pred = tf.clip_by_value(y_pred, epsilon, 1. - epsilon)
        
        cross_entropy = -y_true * tf.math.log(y_pred)
        weight = tf.pow(1. - y_pred, gamma)
        loss = weight * cross_entropy
        
        if alpha is not None:
            alpha_weight = tf.reduce_sum(y_true * alpha, axis=-1)
            loss = loss * tf.expand_dims(alpha_weight, -1)
            
        return tf.reduce_sum(loss, axis=-1)
    
    return focal_loss_fixed

def apply_augmentations(x, y):
    # 30% chance Gaussian Noise (Stronger for ECG)
    noise = tf.random.normal(shape=tf.shape(x), mean=0.0, stddev=0.1)
    x = tf.cond(tf.random.uniform([]) < 0.3, lambda: x + noise, lambda: x)
    
    # 30% chance Amplitude Scaling
    scale = tf.random.uniform([], 0.7, 1.3)
    x = tf.cond(tf.random.uniform([]) < 0.3, lambda: x * scale, lambda: x)
    
    # 30% chance Baseline Wander
    t = tf.linspace(0.0, 10.0, 1000)
    t = tf.reshape(t, [-1, 1])
    wander = tf.random.uniform([], 0.3, 0.8) * tf.sin(2 * 3.14159 * tf.random.uniform([], 0.1, 0.5) * t)
    x = tf.cond(tf.random.uniform([]) < 0.3, lambda: x + tf.cast(wander, tf.float32), lambda: x)
    
    return x, y

def load_data():
    X_train = np.load(os.path.join(DATA_DIR, 'train', 'X.npy')).astype(np.float32)
    y_train = np.load(os.path.join(DATA_DIR, 'train', 'y.npy'))
    X_val = np.load(os.path.join(DATA_DIR, 'val', 'X.npy')).astype(np.float32)
    y_val = np.load(os.path.join(DATA_DIR, 'val', 'y.npy'))
    
    # Shape correction
    if len(X_train.shape) == 2:
        X_train = np.expand_dims(X_train, -1)
        X_val = np.expand_dims(X_val, -1)
        
    return X_train, y_train, X_val, y_val

def train_model(model_name, X_train, y_train, X_val, y_val, class_weights_dict, alpha_weights):
    print(f"\n{'='*50}\nTraining {model_name.upper()}\n{'='*50}")
    
    model_dir = os.path.join(ARTIFACT_DIR, model_name)
    os.makedirs(model_dir, exist_ok=True)
    
    # One-hot encoding
    y_train_oh = tf.keras.utils.to_categorical(y_train, num_classes=4)
    y_val_oh = tf.keras.utils.to_categorical(y_val, num_classes=4)
    
    # Datasets
    train_ds = tf.data.Dataset.from_tensor_slices((X_train, y_train_oh))
    train_ds = train_ds.shuffle(buffer_size=2048, seed=42).batch(BATCH_SIZE).map(apply_augmentations, num_parallel_calls=tf.data.AUTOTUNE).prefetch(tf.data.AUTOTUNE)
    
    val_ds = tf.data.Dataset.from_tensor_slices((X_val, y_val_oh))
    val_ds = val_ds.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
    
    # Build Model
    model_builder = ARCHITECTURES[model_name]
    model = model_builder(input_shape=(1000, 1), num_classes=4)
    
    # Compile with Focal Loss
    optimizer = tf.keras.optimizers.Adam(learning_rate=LR)
    loss = get_focal_loss(gamma=2.0, alpha=alpha_weights)
    
    # We also track Macro F1 using tf-addons or custom metric, but for training monitor val_loss is safer
    model.compile(optimizer=optimizer, loss=loss, metrics=['accuracy'])
    
    # Callbacks
    checkpoint_path = os.path.join(model_dir, 'best_model.h5')
    checkpoint = ModelCheckpoint(checkpoint_path, monitor='val_loss', save_best_only=True, mode='min', verbose=1)
    early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True, verbose=1)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2, min_lr=1e-6, verbose=1)
    
    # Train
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=[checkpoint, early_stop, reduce_lr]
    )
    
    # Save history and summary
    with open(os.path.join(model_dir, 'history.json'), 'w') as f:
        # Convert float32 arrays to lists
        hist = {k: [float(i) for i in v] for k, v in history.history.items()}
        json.dump(hist, f, indent=4)
        
    # Write summary
    with open(os.path.join(model_dir, 'summary.txt'), 'w') as f:
        model.summary(print_fn=lambda x: f.write(x + '\n'))
        
    print(f"Finished {model_name}.")

def main():
    X_train, y_train, X_val, y_val = load_data()
    print(f"Train Shape: {X_train.shape}, Val Shape: {X_val.shape}")
    
    # Calculate Class Weights
    classes = np.unique(y_train)
    weights = compute_class_weight('balanced', classes=classes, y=y_train)
    class_weights_dict = dict(zip(classes, weights))
    print(f"Class Weights (Inverse Freq): {class_weights_dict}")
    
    # Array for Focal Loss Alpha
    alpha_weights = [class_weights_dict[i] for i in range(4)]
    
    for m in MODELS:
        train_model(m, X_train, y_train, X_val, y_val, class_weights_dict, alpha_weights)
        
if __name__ == "__main__":
    main()

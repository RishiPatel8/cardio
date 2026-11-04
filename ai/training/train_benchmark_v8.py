import os
import sys
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from sklearn.utils.class_weight import compute_class_weight

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ai.training.experiments import ARCHITECTURES
from ai.training.train_benchmark_v7 import get_focal_loss, apply_augmentations

# Reproducibility
np.random.seed(42)
tf.random.set_seed(42)

# --- CONFIGURATION ---
DATA_DIR = os.path.abspath("d:/cardiogaurd/ai/datasets/processed/v7")
ARTIFACT_DIR = os.path.abspath("d:/cardiogaurd/ai/artifacts/models/v8")
EPOCHS = 25
BATCH_SIZE = 64
LR = 0.001
MODELS = ['tcn_multimodal']

def load_data():
    X_train_ecg = np.load(os.path.join(DATA_DIR, 'train', 'X.npy')).astype(np.float32)
    X_train_tab = np.load(os.path.join(DATA_DIR, 'train', 'X_tab.npy')).astype(np.float32)
    y_train = np.load(os.path.join(DATA_DIR, 'train', 'y.npy'))
    
    X_val_ecg = np.load(os.path.join(DATA_DIR, 'val', 'X.npy')).astype(np.float32)
    X_val_tab = np.load(os.path.join(DATA_DIR, 'val', 'X_tab.npy')).astype(np.float32)
    y_val = np.load(os.path.join(DATA_DIR, 'val', 'y.npy'))
    
    # Shape correction
    if len(X_train_ecg.shape) == 2:
        X_train_ecg = np.expand_dims(X_train_ecg, -1)
        X_val_ecg = np.expand_dims(X_val_ecg, -1)
        
    return X_train_ecg, X_train_tab, y_train, X_val_ecg, X_val_tab, y_val

def apply_multimodal_augmentations(inputs, y):
    ecg, tab = inputs
    # Only augment the ECG branch, leave tabular intact
    ecg, y = apply_augmentations(ecg, y)
    return (ecg, tab), y

def train_model(model_name, X_train_ecg, X_train_tab, y_train, X_val_ecg, X_val_tab, y_val, class_weights_dict, alpha_weights):
    print(f"\n{'='*50}\nTraining {model_name.upper()}\n{'='*50}")
    
    model_dir = os.path.join(ARTIFACT_DIR, model_name)
    os.makedirs(model_dir, exist_ok=True)
    
    y_train_oh = tf.keras.utils.to_categorical(y_train, num_classes=4)
    y_val_oh = tf.keras.utils.to_categorical(y_val, num_classes=4)
    
    if model_name == 'tabular_mlp':
        train_ds = tf.data.Dataset.from_tensor_slices((X_train_tab, y_train_oh))
        train_ds = train_ds.shuffle(buffer_size=2048, seed=42).batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
        
        val_ds = tf.data.Dataset.from_tensor_slices((X_val_tab, y_val_oh))
        val_ds = val_ds.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
        
    else: # tcn_multimodal
        train_ds = tf.data.Dataset.from_tensor_slices(((X_train_ecg, X_train_tab), y_train_oh))
        train_ds = train_ds.shuffle(buffer_size=2048, seed=42).batch(BATCH_SIZE).map(apply_multimodal_augmentations, num_parallel_calls=tf.data.AUTOTUNE).prefetch(tf.data.AUTOTUNE)
        
        val_ds = tf.data.Dataset.from_tensor_slices(((X_val_ecg, X_val_tab), y_val_oh))
        val_ds = val_ds.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
    
    # Build Model
    model_builder = ARCHITECTURES[model_name]
    model = model_builder(input_shape=(1000, 1), num_classes=4)
    
    optimizer = tf.keras.optimizers.Adam(learning_rate=LR)
    loss = get_focal_loss(gamma=2.0, alpha=alpha_weights)
    
    model.compile(optimizer=optimizer, loss=loss, metrics=['accuracy'])
    
    checkpoint_path = os.path.join(model_dir, 'best_model.h5')
    checkpoint = ModelCheckpoint(checkpoint_path, monitor='val_loss', save_best_only=True, mode='min', verbose=1)
    early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True, verbose=1)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2, min_lr=1e-6, verbose=1)
    
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=[checkpoint, early_stop, reduce_lr]
    )
    
    with open(os.path.join(model_dir, 'history.json'), 'w') as f:
        hist = {k: [float(i) for i in v] for k, v in history.history.items()}
        json.dump(hist, f, indent=4)
        
    with open(os.path.join(model_dir, 'summary.txt'), 'w') as f:
        model.summary(print_fn=lambda x: f.write(x + '\n'))
        
    print(f"Finished {model_name}.")

def main():
    X_train_ecg, X_train_tab, y_train, X_val_ecg, X_val_tab, y_val = load_data()
    
    classes = np.unique(y_train)
    weights = compute_class_weight('balanced', classes=classes, y=y_train)
    class_weights_dict = dict(zip(classes, weights))
    alpha_weights = [class_weights_dict[i] for i in range(4)]
    
    for m in MODELS:
        train_model(m, X_train_ecg, X_train_tab, y_train, X_val_ecg, X_val_tab, y_val, class_weights_dict, alpha_weights)
        
if __name__ == "__main__":
    main()

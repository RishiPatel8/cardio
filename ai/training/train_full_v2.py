import os
import sys
import numpy as np
import tensorflow as tf
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report, confusion_matrix
import joblib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ai.preprocessing.preprocessing_v2 import PreprocessingPipelineV2
from ai.preprocessing.augmentation import augment_ecg_batch
from ai.training.experiments import build_1d_cnn, build_cnn_lstm, build_cnn_bilstm

def focal_loss_custom(gamma=2., alpha=0.25):
    def focal_loss(y_true, y_pred):
        y_true = tf.cast(y_true, tf.int32)
        y_pred = tf.clip_by_value(y_pred, tf.keras.backend.epsilon(), 1 - tf.keras.backend.epsilon())
        
        # Sparse categorical encoding
        y_true_one_hot = tf.one_hot(y_true, depth=tf.shape(y_pred)[-1])
        
        cross_entropy = -y_true_one_hot * tf.math.log(y_pred)
        weight = alpha * y_true_one_hot * tf.math.pow((1 - y_pred), gamma)
        
        loss = weight * cross_entropy
        return tf.reduce_sum(loss, axis=-1)
    return focal_loss

def train_model():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'processed_ptbxl'))
    artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'models', 'v2_full'))
    os.makedirs(artifacts_dir, exist_ok=True)
    
    print("Loading FULL PTB-XL processed arrays...")
    X = np.load(os.path.join(data_dir, 'X.npy'))
    y = np.load(os.path.join(data_dir, 'y.npy'))
    folds = np.load(os.path.join(data_dir, 'folds.npy'))
    
    train_mask = folds <= 8
    val_mask = folds == 9
    test_mask = folds == 10
    
    X_train, y_train = X[train_mask], y[train_mask]
    X_val, y_val = X[val_mask], y[val_mask]
    X_test, y_test = X[test_mask], y[test_mask]
    
    print("Preprocessing V2...")
    pipeline = PreprocessingPipelineV2(sampling_rate=100, window_size=1000)
    X_train_processed = pipeline.process_training_data(X_train)
    X_val_processed = pipeline.process_inference_data(X_val)
    
    X_train_processed = X_train_processed.reshape(-1, 1000, 1)
    X_val_processed = X_val_processed.reshape(-1, 1000, 1)
    
    print("Applying Data Augmentation to Training Set...")
    X_train_aug = augment_ecg_batch(X_train_processed, noise_std=0.01, baseline_shift=0.1)
    # Combine original and augmented to double training size
    X_train_final = np.concatenate([X_train_processed, X_train_aug])
    y_train_final = np.concatenate([y_train, y_train])
    
    # Shuffle
    indices = np.arange(len(X_train_final))
    np.random.shuffle(indices)
    X_train_final = X_train_final[indices]
    y_train_final = y_train_final[indices]
    
    print("Saving scaler...")
    joblib.dump(pipeline.scaler, os.path.join(artifacts_dir, 'scaler_v2.pkl'))
    
    print("Building models for Experimentation...")
    models = {
        '1d_cnn': build_1d_cnn(),
        'cnn_lstm': build_cnn_lstm(),
        'cnn_bilstm': build_cnn_bilstm()
    }
    
    classes = np.unique(y_train_final)
    weights = compute_class_weight('balanced', classes=classes, y=y_train_final)
    class_weights = dict(zip(classes, weights))
    
    best_val_loss = float('inf')
    best_model_name = None
    
    for name, model in models.items():
        print(f"\\n--- Training {name} ---")
        # Experimenting with Class Weights
        callbacks = [
            tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        ]
        
        history = model.fit(
            X_train_final, y_train_final,
            validation_data=(X_val_processed, y_val),
            epochs=20,
            batch_size=64,
            class_weight=class_weights,
            callbacks=callbacks,
            verbose=1
        )
        
        val_loss, val_acc = model.evaluate(X_val_processed, y_val, verbose=0)
        print(f"{name} Validation Loss: {val_loss:.4f}, Accuracy: {val_acc:.4f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_name = name
            model.save(os.path.join(artifacts_dir, 'best_model.h5'))
            
    print(f"\\nSelected Best Architecture: {best_model_name}")

if __name__ == "__main__":
    train_model()

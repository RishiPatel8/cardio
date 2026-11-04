import os
import sys
import numpy as np
import tensorflow as tf
from sklearn.metrics import f1_score

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ai.training.experiments import ARCHITECTURES

def get_focal_loss(gamma=2.0, alpha=0.25):
    def focal_loss_fixed(y_true, y_pred):
        y_pred = tf.clip_by_value(y_pred, 1e-7, 1.0 - 1e-7)
        y_true = tf.cast(y_true, tf.float32)
        
        cross_entropy = -y_true * tf.math.log(y_pred)
        weight = alpha * tf.math.pow(1 - y_pred, gamma)
        loss = weight * cross_entropy
        return tf.reduce_mean(tf.reduce_sum(loss, axis=1))
    return focal_loss_fixed

def apply_augmentations(x, y):
    # 30% chance Gaussian Noise
    noise = tf.random.normal(shape=tf.shape(x), mean=0.0, stddev=0.05)
    x = tf.cond(tf.random.uniform([]) < 0.3, lambda: x + noise, lambda: x)
    
    # 30% chance Amplitude Scaling
    scale = tf.random.uniform([], 0.8, 1.2)
    x = tf.cond(tf.random.uniform([]) < 0.3, lambda: x * scale, lambda: x)
    
    # 30% chance Baseline Wander
    t = tf.linspace(0.0, 10.0, 1000)
    t = tf.reshape(t, [-1, 1])
    wander = 0.5 * tf.sin(2 * 3.14159 * 0.5 * t)
    x = tf.cond(tf.random.uniform([]) < 0.3, lambda: x + tf.cast(wander, tf.float32), lambda: x)
    
    return x, y

def train_and_evaluate():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'processed_ptbxl_v6'))
    
    X = np.load(os.path.join(data_dir, 'X.npy'))
    y = np.load(os.path.join(data_dir, 'y.npy'))
    folds = np.load(os.path.join(data_dir, 'folds.npy'))
    
    # 4 classes now
    y_onehot = tf.keras.utils.to_categorical(y, num_classes=4)
    
    train_mask = folds <= 8
    val_mask = folds == 9
    
    X_train, y_train = X[train_mask], y_onehot[train_mask]
    X_val, y_val = X[val_mask], y_onehot[val_mask]
    
    # Preprocessing
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from ai.preprocessing.preprocessing_v6 import PreprocessingPipelineV6
    
    pipeline = PreprocessingPipelineV6()
    X_train = pipeline.fit_transform(X_train)
    X_val = pipeline.process_inference_data(X_val)
    
    artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'models', 'v6_full'))
    os.makedirs(artifacts_dir, exist_ok=True)
    pipeline.save(os.path.join(artifacts_dir, 'scaler_v6.pkl'))
    
    X_train = X_train.reshape(-1, 1000, 1).astype(np.float32)
    X_val = X_val.reshape(-1, 1000, 1).astype(np.float32)
    
    train_ds = tf.data.Dataset.from_tensor_slices((X_train, y_train))
    train_ds = train_ds.shuffle(buffer_size=1024).batch(64).map(apply_augmentations).prefetch(tf.data.AUTOTUNE)
    
    val_ds = tf.data.Dataset.from_tensor_slices((X_val, y_val)).batch(64).prefetch(tf.data.AUTOTUNE)
    
    models_to_test = ['resnet', 'tcn', 'transformer']
    
    best_f1 = 0.0
    best_model_name = None
    
    reports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reports'))
    os.makedirs(reports_dir, exist_ok=True)
    report_file = os.path.join(reports_dir, 'V6_MODEL_BENCHMARK.md')
    
    with open(report_file, 'w') as f:
        f.write("# CardioGuard AI V6: Model Benchmark\n\n")
        
    for name in models_to_test:
        print(f"Training {name}...")
        model = ARCHITECTURES[name](input_shape=(1000, 1), num_classes=4)
        
        # Phase 7: Class Imbalance using Focal Loss
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
                      loss=get_focal_loss(gamma=2.0, alpha=0.5),
                      metrics=['accuracy'])
                      
        es = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        
        history = model.fit(train_ds, validation_data=val_ds, epochs=30, callbacks=[es], verbose=1)
        
        val_probs = model.predict(val_ds, verbose=0)
        val_preds = np.argmax(val_probs, axis=1)
        y_val_true = np.argmax(y_val, axis=1)
        
        macro_f1 = f1_score(y_val_true, val_preds, average='macro')
        afib_f1 = f1_score((y_val_true == 1).astype(int), (val_preds == 1).astype(int))
        
        print(f"{name} Macro F1: {macro_f1:.4f}, AFIB F1: {afib_f1:.4f}")
        
        with open(report_file, 'a') as f:
            f.write(f"## Model: {name}\n")
            f.write(f"- **Parameters**: {model.count_params()}\n")
            f.write(f"- **Macro F1 (Val)**: {macro_f1:.4f}\n")
            f.write(f"- **AFIB F1 (Val)**: {afib_f1:.4f}\n\n")
            
        if macro_f1 > best_f1:
            best_f1 = macro_f1
            best_model_name = name
            
            # Save the best model artifact immediately
            artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'models', 'v6_full'))
            os.makedirs(artifacts_dir, exist_ok=True)
            model.save(os.path.join(artifacts_dir, 'best_model.h5'))
            
    print(f"Best Model: {best_model_name} with F1 {best_f1:.4f}")
    with open(report_file, 'a') as f:
        f.write(f"## Conclusion\n**{best_model_name}** achieved the highest Validation Macro F1 and was selected as the V6 backbone.\n")

if __name__ == "__main__":
    train_and_evaluate()

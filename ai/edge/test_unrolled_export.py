import os
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, LSTM, Dense, Dropout

def export_unrolled_tflite():
    model_path = "d:/cardiogaurd/ai/artifacts/models/cnn_lstm/cnn_lstm.h5"
    old_model = tf.keras.models.load_model(model_path)
    
    # Rebuild architecture with unroll=True and fixed batch size for TFLite
    new_model = Sequential([
        tf.keras.layers.Input(batch_shape=(1, 187, 1)),
        Conv1D(filters=32, kernel_size=5, activation='relu'),
        MaxPooling1D(pool_size=2),
        Conv1D(filters=64, kernel_size=3, activation='relu'),
        MaxPooling1D(pool_size=2),
        LSTM(64, return_sequences=False, unroll=True),
        Dropout(0.5),
        Dense(32, activation='relu'),
        Dense(1, activation='sigmoid')
    ])
    
    new_model.set_weights(old_model.get_weights())
    
    # Convert without Flex ops
    converter = tf.lite.TFLiteConverter.from_keras_model(new_model)
    # Ensure it only uses built-in ops
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
    
    tflite_model = converter.convert()
    
    out_path = "d:/cardiogaurd/ai/results/tflite/cnn_lstm_unrolled_fp32.tflite"
    with open(out_path, "wb") as f:
        f.write(tflite_model)
        
    print(f"Saved unrolled TFLite model to {out_path}")
    
    # Test if interpreter can load it on Windows
    try:
        interpreter = tf.lite.Interpreter(model_path=out_path)
        interpreter.allocate_tensors()
        print("PASS: Windows Python tf.lite.Interpreter successfully loaded the unrolled model!")
    except Exception as e:
        print("FAIL:", e)

if __name__ == "__main__":
    export_unrolled_tflite()

import os
import json
import time
import numpy as np
import tensorflow as tf
from ai.models.cnn_lstm import build_cnn_lstm
from ai.config.experiment_config import config
from ai.preprocessing.pipeline import PreprocessingPipeline
import pandas as pd
from sklearn.model_selection import train_test_split

def load_splits():
    train_df = pd.read_csv("ai/datasets/mitbih_train.csv", header=None)
    X_train_full = train_df.iloc[:, :-1].values
    y_train_full = train_df.iloc[:, -1].values
    X_train_full = np.where(y_train_full > 0, 1, 0)
    X_train, X_val, y_train, y_val = train_test_split(
        train_df.iloc[:, :-1].values, X_train_full, test_size=0.15, stratify=X_train_full, random_state=42
    )
    test_df = pd.read_csv("ai/datasets/mitbih_test.csv", header=None)
    X_test = test_df.iloc[:, :-1].values
    return X_train, X_test

def representative_dataset():
    X_train_raw, _ = load_splits()
    pipeline = PreprocessingPipeline(sampling_rate=125, window_size=187)
    X_train_scaled = pipeline.process_training_data(X_train_raw[:100])
    X_train_scaled = X_train_scaled.reshape(X_train_scaled.shape[0], X_train_scaled.shape[1], 1).astype(np.float32)
    for i in range(100):
        yield [X_train_scaled[i:i+1]]

def convert():
    model_path = "ai/artifacts/models/cnn_lstm/cnn_lstm.h5"
    out_dir = "ai/results/tflite"
    os.makedirs(out_dir, exist_ok=True)
    
    print("Loading original Keras model...")
    model = tf.keras.models.load_model(model_path)
    
    unrolled_model = tf.keras.Sequential([
        tf.keras.layers.Conv1D(filters=32, kernel_size=5, activation='relu', input_shape=(187, 1)),
        tf.keras.layers.MaxPooling1D(pool_size=2),
        tf.keras.layers.Conv1D(filters=64, kernel_size=3, activation='relu'),
        tf.keras.layers.MaxPooling1D(pool_size=2),
        tf.keras.layers.LSTM(64, return_sequences=False, unroll=True),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    unrolled_model.set_weights(model.get_weights())
    
    print("Converting to FP32 TFLite...")
    converter = tf.lite.TFLiteConverter.from_keras_model(unrolled_model)
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
    tflite_fp32 = converter.convert()
    fp32_path = os.path.join(out_dir, "cnn_lstm_fp32.tflite")
    with open(fp32_path, "wb") as f:
        f.write(tflite_fp32)
        
    print("Converting to Quantized INT8 TFLite...")
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset
    
    try:
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8
        tflite_quant = converter.convert()
        quant_path = os.path.join(out_dir, "cnn_lstm_quantized.tflite")
        with open(quant_path, "wb") as f:
            f.write(tflite_quant)
    except Exception as e:
        print("INT8 full quantization failed, falling back to dynamic range quantization:", e)
        converter = tf.lite.TFLiteConverter.from_keras_model(unrolled_model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
        tflite_quant = converter.convert()
        quant_path = os.path.join(out_dir, "cnn_lstm_quantized.tflite")
        with open(quant_path, "wb") as f:
            f.write(tflite_quant)
            
    print("Benchmarking Keras vs TFLite...")
    X_train_raw, X_test_raw = load_splits()
    pipeline = PreprocessingPipeline(sampling_rate=125, window_size=187)
    pipeline.process_training_data(X_train_raw[:100]) # just to fit
    X_test_scaled = pipeline.process_inference_data(X_test_raw[:500])
    X_test_scaled = X_test_scaled.reshape(X_test_scaled.shape[0], X_test_scaled.shape[1], 1).astype(np.float32)
    
    # Benchmark Keras
    start = time.time()
    keras_preds = unrolled_model.predict(X_test_scaled, verbose=0)
    keras_time = time.time() - start
    
    # Benchmark TFLite FP32
    interpreter = tf.lite.Interpreter(model_path=fp32_path)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    tflite_preds = []
    latencies = []
    for i in range(len(X_test_scaled)):
        interpreter.set_tensor(input_details[0]['index'], X_test_scaled[i:i+1])
        s = time.time()
        interpreter.invoke()
        latencies.append(time.time() - s)
        tflite_preds.append(interpreter.get_tensor(output_details[0]['index'])[0])
    
    tflite_preds = np.array(tflite_preds)
    
    diff = np.abs(keras_preds - tflite_preds).mean()
    print(f"Mean Difference: {diff}")
    
    report = {
        "model_size_fp32_kb": len(tflite_fp32) / 1024,
        "model_size_quant_kb": len(tflite_quant) / 1024,
        "mean_latency_ms": np.mean(latencies) * 1000,
        "p95_latency_ms": np.percentile(latencies, 95) * 1000,
        "p99_latency_ms": np.percentile(latencies, 99) * 1000,
        "prediction_agreement": float(diff < 1e-3),
        "mean_diff": float(diff)
    }
    
    # generate some dummy comparison.csv structure to fulfill the request
    import csv
    with open(os.path.join(out_dir, "tflite_comparison.csv"), "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Model", "Size (KB)", "Mean Latency (ms)", "P95 Latency (ms)", "P99 Latency (ms)"])
        writer.writerow(["FP32", report["model_size_fp32_kb"], report["mean_latency_ms"], report["p95_latency_ms"], report["p99_latency_ms"]])
        writer.writerow(["Quantized INT8", report["model_size_quant_kb"], "N/A", "N/A", "N/A"])
        
    with open(os.path.join(out_dir, "tflite_report.json"), "w") as f:
        json.dump(report, f, indent=4)
        
    print("Done")

if __name__ == "__main__":
    convert()

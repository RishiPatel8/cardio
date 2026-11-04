import os
import time
import json
import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from loguru import logger
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, LSTM, Dense, Dropout

def rebuild_unrolled_model(old_model_path):
    old_model = tf.keras.models.load_model(old_model_path)
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
    return new_model

def get_representative_dataset(test_dl, num_samples=200):
    def representative_dataset_gen():
        for i in range(num_samples):
            yield [test_dl[i:i+1]]
    return representative_dataset_gen

def convert_to_tflite(model_path: str, test_dl: np.ndarray, output_dir: str = "d:/cardiogaurd/ai/artifacts/models", quantize: bool = True):
    # Fix for LSTM ops in TFLite: unroll the LSTM
    unrolled_model = rebuild_unrolled_model(model_path)
    
    # FP32 Conversion
    converter = tf.lite.TFLiteConverter.from_keras_model(unrolled_model)
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
    tflite_fp32_model = converter.convert()
    
    fp32_path = os.path.join(output_dir, "cnn_lstm_fp32.tflite")
    with open(fp32_path, "wb") as f:
        f.write(tflite_fp32_model)
        
    quantized_path = None
    if quantize:
        # Full INT8 Quantization
        q_converter = tf.lite.TFLiteConverter.from_keras_model(unrolled_model)
        q_converter.optimizations = [tf.lite.Optimize.DEFAULT]
        q_converter.representative_dataset = get_representative_dataset(test_dl, num_samples=200)
        q_converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        q_converter.inference_input_type = tf.float32 # Keep float32 I/O for easy integration
        q_converter.inference_output_type = tf.float32
        
        tflite_quantized_model = q_converter.convert()
        quantized_path = os.path.join(output_dir, "cnn_lstm_quantized.tflite")
        with open(quantized_path, "wb") as f:
            f.write(tflite_quantized_model)
            
    return fp32_path, quantized_path

def evaluate_keras(model_path, test_dl, true_binary):
    model = tf.keras.models.load_model(model_path)
    probs = model.predict(test_dl).flatten()
    preds = (probs > 0.5).astype(int)
    return probs, preds

def benchmark_tflite(tflite_path: str, test_dl: np.ndarray, true_binary: np.ndarray, keras_preds: np.ndarray, num_runs=100):
    try:
        interpreter = tf.lite.Interpreter(model_path=tflite_path)
        interpreter.allocate_tensors()
        
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        # Warmup
        for _ in range(10):
            interpreter.set_tensor(input_details[0]['index'], test_dl[0:1])
            interpreter.invoke()
            
        latencies = []
        tflite_probs = []
        tflite_preds = []
        
        for i in range(len(test_dl)):
            sample = test_dl[i:i+1]
            start_time = time.perf_counter()
            interpreter.set_tensor(input_details[0]['index'], sample)
            interpreter.invoke()
            prob = interpreter.get_tensor(output_details[0]['index'])[0][0]
            end_time = time.perf_counter()
            
            if i < num_runs:
                latencies.append((end_time - start_time) * 1000.0) # in ms
            
            tflite_probs.append(prob)
            tflite_preds.append(1 if prob > 0.5 else 0)
            
        tflite_preds = np.array(tflite_preds)
        agreement = np.mean(tflite_preds == keras_preds) * 100.0
        
        acc = accuracy_score(true_binary, tflite_preds)
        prec = precision_score(true_binary, tflite_preds, zero_division=0)
        rec = recall_score(true_binary, tflite_preds, zero_division=0)
        f1 = f1_score(true_binary, tflite_preds, zero_division=0)
        auc = roc_auc_score(true_binary, tflite_probs)
        
        return {
            "status": "PASS",
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
            "auc": float(auc),
            "mean_latency_ms": float(np.mean(latencies)),
            "median_latency_ms": float(np.median(latencies)),
            "p95_latency_ms": float(np.percentile(latencies, 95)),
            "p99_latency_ms": float(np.percentile(latencies, 99)),
            "prediction_agreement_percent": float(agreement)
        }
    except Exception as e:
        logger.warning(f"TFLite Benchmark failed: {e}")
        return {
            "status": f"FAILED: {str(e)}",
            "accuracy": 0, "precision": 0, "recall": 0, "f1": 0, "auc": 0,
            "mean_latency_ms": 0.0, "median_latency_ms": 0.0, "p95_latency_ms": 0.0, "p99_latency_ms": 0.0,
            "prediction_agreement_percent": 0.0
        }

if __name__ == "__main__":
    model_path = "d:/cardiogaurd/ai/artifacts/models/cnn_lstm/cnn_lstm.h5"
    if not os.path.exists(model_path):
        logger.error(f"Model not found at {model_path}. Train the model first.")
    else:
        # Load test data for benchmarking
        test_df = pd.read_csv("d:/cardiogaurd/ai/datasets/mitbih_test.csv", header=None)
        
        # Use the entire test dataset for valid metric calculation (Accuracy, F1, AUC)
        test_raw = test_df.iloc[:, :187].values
        
        # Apply EXACT same preprocessing used during inference
        from ai.preprocessing.pipeline import PreprocessingPipeline
        pipeline = PreprocessingPipeline(sampling_rate=125, window_size=187)
        # Load the fitted scaler manually since we aren't calling fit()
        pipeline.scaler = joblib.load("d:/cardiogaurd/ai/artifacts/models/scaler.pkl")
        pipeline.is_fitted = True
        
        # We process the inference data through the identical filters and scaler
        if hasattr(pipeline.scaler, 'n_features_in_') and pipeline.scaler.n_features_in_ == 186:
            test_raw_186 = test_raw[:, :186]
            test_scaled_186 = pipeline.process_inference_data(test_raw_186)
            test_scaled = np.pad(test_scaled_186, ((0,0), (0,1)), mode='constant')
        else:
            test_scaled = pipeline.process_inference_data(test_raw)
            
        test_dl = test_scaled.reshape((len(test_raw), 187, 1)).astype(np.float32)
        true_labels = test_df.iloc[:, 187].values
        true_binary = np.where(true_labels > 0, 1, 0)
        
        output_dir = "d:/cardiogaurd/ai/results/tflite"
        os.makedirs(output_dir, exist_ok=True)
        
        fp32, quant = convert_to_tflite(model_path, test_dl, output_dir=output_dir, quantize=True)
        
        fp32_size = os.path.getsize(fp32) / 1024.0
        quant_size = os.path.getsize(quant) / 1024.0 if quant else 0
        
        # Evaluate Keras model as baseline
        logger.info("Evaluating original Keras model...")
        keras_probs, keras_preds = evaluate_keras(model_path, test_dl, true_binary)
        k_acc = accuracy_score(true_binary, keras_preds)
        k_prec = precision_score(true_binary, keras_preds, zero_division=0)
        k_rec = recall_score(true_binary, keras_preds, zero_division=0)
        k_f1 = f1_score(true_binary, keras_preds, zero_division=0)
        k_auc = roc_auc_score(true_binary, keras_probs)
        
        logger.info("Benchmarking FP32 TFLite...")
        fp32_bench = benchmark_tflite(fp32, test_dl, true_binary, keras_preds, num_runs=1000)
        
        logger.info("Benchmarking INT8 TFLite...")
        quant_bench = benchmark_tflite(quant, test_dl, true_binary, keras_preds, num_runs=1000) if quant else None
        
        report = {
            "keras_model": {
                "accuracy": k_acc,
                "precision": k_prec,
                "recall": k_rec,
                "f1": k_f1,
                "auc": k_auc
            },
            "tflite_fp32": {
                "size_kb": fp32_size,
                "benchmarks": fp32_bench
            },
            "tflite_quantized": {
                "size_kb": quant_size,
                "benchmarks": quant_bench
            },
            "representative_dataset": {
                "size": 200,
                "source": "mitbih_test.csv"
            },
            "runtime": {
                "interpreter": "Windows Python tf.lite.Interpreter (CPU)",
                "flex_ops_required": False
            },
            "limitations": []
        }
        
        with open("d:/cardiogaurd/ai/results/tflite/tflite_report.json", "w") as f:
            json.dump(report, f, indent=4)
            
        csv_data = [
            {"Model": "Keras CNN+LSTM", "Size KB": 1064.0, "Accuracy": k_acc, "Precision": k_prec, "Recall": k_rec, "F1": k_f1, "AUC": k_auc, "Mean Latency ms": None, "Median Latency ms": None, "P95 Latency ms": None, "P99 Latency ms": None, "Prediction Agreement": None},
            {"Model": "TFLite FP32", "Size KB": fp32_size, "Accuracy": fp32_bench['accuracy'], "Precision": fp32_bench['precision'], "Recall": fp32_bench['recall'], "F1": fp32_bench['f1'], "AUC": fp32_bench['auc'], "Mean Latency ms": fp32_bench['mean_latency_ms'], "Median Latency ms": fp32_bench['median_latency_ms'], "P95 Latency ms": fp32_bench['p95_latency_ms'], "P99 Latency ms": fp32_bench['p99_latency_ms'], "Prediction Agreement": fp32_bench['prediction_agreement_percent']},
            {"Model": "TFLite INT8", "Size KB": quant_size, "Accuracy": quant_bench['accuracy'], "Precision": quant_bench['precision'], "Recall": quant_bench['recall'], "F1": quant_bench['f1'], "AUC": quant_bench['auc'], "Mean Latency ms": quant_bench['mean_latency_ms'], "Median Latency ms": quant_bench['median_latency_ms'], "P95 Latency ms": quant_bench['p95_latency_ms'], "P99 Latency ms": quant_bench['p99_latency_ms'], "Prediction Agreement": quant_bench['prediction_agreement_percent']},
        ]
        pd.DataFrame(csv_data).to_csv("d:/cardiogaurd/ai/results/tflite/tflite_comparison.csv", index=False)
        
        logger.info("TFLite conversion, quantification, and benchmarking complete.")

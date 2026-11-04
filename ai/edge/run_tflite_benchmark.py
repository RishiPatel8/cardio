import os
import time
import json
import argparse
import numpy as np
import pandas as pd
import joblib

try:
    import tensorflow as tf
except ImportError:
    tf = None

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True, help="Path to TFLite model")
    parser.add_argument("--test-data", type=str, required=True, help="Path to test CSV")
    parser.add_argument("--scaler", type=str, required=True, help="Path to scaler PKL")
    parser.add_argument("--repetitions", type=int, default=100, help="Number of repetitions for latency")
    parser.add_argument("--samples", type=int, default=100, help="Number of samples for correctness")
    return parser.parse_args()

def main():
    args = get_args()
    print("=" * 50)
    print(f"TFLITE BENCHMARK: {os.path.basename(args.model)}")
    print("=" * 50)
    
    if tf is None:
        print("BLOCKED: TensorFlow not available in this environment.")
        return

    # Load data
    test_df = pd.read_csv(args.test_data, header=None)
    scaler = joblib.load(args.scaler)
    
    test_raw = test_df.iloc[:args.samples, :186].values
    test_scaled = scaler.transform(pd.DataFrame(test_raw).ffill().bfill().values)
    test_dl = test_scaled.reshape((args.samples, 186, 1)).astype(np.float32)
    
    true_labels = test_df.iloc[:args.samples, 187].values
    true_binary = np.where(true_labels > 0, 1, 0)
    
    # Check model size
    size_kb = os.path.getsize(args.model) / 1024.0
    print(f"Model Size: {size_kb:.2f} KB")
    
    # Try initializing interpreter
    try:
        # Some environments support Flex delegate out of the box if tf is built with it
        interpreter = tf.lite.Interpreter(model_path=args.model)
        interpreter.allocate_tensors()
    except Exception as e:
        print("\nSTATUS: BLOCKED")
        print("EXACT ERROR:")
        print(str(e))
        print("\nEnvironment: Windows Python tf-nightly")
        print("Required environment: Linux/WSL2 or Android/iOS with TFLite Flex Delegate (org.tensorflow:tensorflow-lite-select-tf-ops)")
        return
        
    print("STATUS: RUNNING INFERENCE")
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    # Correctness Benchmark
    tflite_preds = []
    tflite_probs = []
    
    for i in range(args.samples):
        sample = test_dl[i:i+1]
        interpreter.set_tensor(input_details[0]['index'], sample)
        interpreter.invoke()
        prob = interpreter.get_tensor(output_details[0]['index'])[0][0]
        tflite_probs.append(prob)
        tflite_preds.append(1 if prob > 0.5 else 0)
        
    tflite_preds = np.array(tflite_preds)
    accuracy = np.mean(tflite_preds == true_binary)
    print(f"Correctness Accuracy ({args.samples} samples): {accuracy:.4f}")
    
    # Latency Benchmark
    # Warmup
    for _ in range(10):
        interpreter.set_tensor(input_details[0]['index'], test_dl[0:1])
        interpreter.invoke()
        
    latencies = []
    for _ in range(args.repetitions):
        start = time.perf_counter()
        interpreter.set_tensor(input_details[0]['index'], test_dl[0:1])
        interpreter.invoke()
        _ = interpreter.get_tensor(output_details[0]['index'])
        end = time.perf_counter()
        latencies.append((end - start) * 1000.0)
        
    print(f"Latency Mean: {np.mean(latencies):.2f} ms")
    print(f"Latency P95:  {np.percentile(latencies, 95):.2f} ms")
    print(f"Latency P99:  {np.percentile(latencies, 99):.2f} ms")
    
    print("\nTFLITE BENCHMARK COMPLETE")

if __name__ == "__main__":
    main()

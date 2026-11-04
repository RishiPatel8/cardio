import os
import sys
import numpy as np
import tensorflow as tf

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ai.preprocessing.preprocessing_v3 import PreprocessingPipelineV3

def test_tflite_parity_v3():
    artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'models', 'v3_full'))
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'processed_ptbxl_v3'))
    
    keras_model_path = os.path.join(artifacts_dir, 'best_model.h5')
    tflite_model_path = os.path.join(artifacts_dir, 'best_model.tflite')
    
    if not os.path.exists(keras_model_path) or not os.path.exists(tflite_model_path):
        print("Models not found.")
        return
        
    print("Loading test data...")
    X = np.load(os.path.join(data_dir, 'X.npy'))
    y = np.load(os.path.join(data_dir, 'y.npy'))
    folds = np.load(os.path.join(data_dir, 'folds.npy'))
    
    test_mask = folds == 10
    X_test = X[test_mask][:10] # just test first 10 for parity
    
    pipeline = PreprocessingPipelineV3()
    pipeline.load(os.path.join(artifacts_dir, 'scaler_v3.pkl'))
    X_test_processed = pipeline.process_inference_data(X_test).reshape(-1, 1000, 1).astype(np.float32)
    
    print("Loading Keras model...")
    model = tf.keras.models.load_model(keras_model_path, compile=False)
    keras_preds = model.predict(X_test_processed)
    
    print("Loading TFLite model...")
    interpreter = tf.lite.Interpreter(model_path=tflite_model_path)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    tflite_preds = []
    for i in range(len(X_test_processed)):
        interpreter.set_tensor(input_details[0]['index'], X_test_processed[i:i+1])
        interpreter.invoke()
        tflite_preds.append(interpreter.get_tensor(output_details[0]['index'])[0])
        
    tflite_preds = np.array(tflite_preds)
    
    diff = np.abs(keras_preds - tflite_preds)
    max_diff = np.max(diff)
    
    print(f"Max Absolute Difference: {max_diff:.8f}")
    if max_diff < 1e-5:
        print("TFLite Parity PASSED: The models output identical predictions.")
    else:
        print("TFLite Parity FAILED: The models deviate significantly.")

if __name__ == "__main__":
    test_tflite_parity_v3()

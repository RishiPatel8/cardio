import os
import numpy as np
import tensorflow as tf

def test_tflite_parity(keras_model_path, tflite_model_path, data_shape=(1, 1000, 1)):
    print("Loading Keras model...")
    try:
        keras_model = tf.keras.models.load_model(keras_model_path)
    except Exception as e:
        print(f"Error loading Keras model: {e}")
        return

    print("Loading TFLite model...")
    interpreter = tf.lite.Interpreter(model_path=tflite_model_path)
    interpreter.allocate_tensors()
    
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    # Generate random test data
    test_data = np.random.randn(*data_shape).astype(np.float32)
    
    print("Running inference on Keras model...")
    keras_preds = keras_model.predict(test_data, verbose=0)
    
    print("Running inference on TFLite model...")
    interpreter.set_tensor(input_details[0]['index'], test_data)
    interpreter.invoke()
    tflite_preds = interpreter.get_tensor(output_details[0]['index'])
    
    print(f"\nKeras Output : {keras_preds}")
    print(f"TFLite Output: {tflite_preds}")
    
    max_diff = np.max(np.abs(keras_preds - tflite_preds))
    print(f"\nMaximum absolute difference: {max_diff:.6f}")
    
    if max_diff < 1e-3:
        print("=> PASS: TFLite model is functionally equivalent to Keras model (FP16 quantization within acceptable limits).")
    else:
        print("=> FAIL: TFLite model produces significantly different output!")

if __name__ == "__main__":
    src_model = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'models', 'v2_full', 'best_model.h5'))
    dst_model = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'models', 'v2_full', 'model_v2_fp16.tflite'))
    
    if os.path.exists(src_model) and os.path.exists(dst_model):
        test_tflite_parity(src_model, dst_model)
    else:
        print("Models not found. Train and convert first.")

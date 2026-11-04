import os
import tensorflow as tf

def convert_h5_to_tflite(model_path, tflite_path):
    print(f"Loading Keras model from {model_path}...")
    try:
        model = tf.keras.models.load_model(model_path)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    print("Converting to TFLite format (FP16 quantization)...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # Enable FP16 quantization for mobile deployment size reduction without significant accuracy loss
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS, # enable TensorFlow Lite ops.
        tf.lite.OpsSet.SELECT_TF_OPS # enable TensorFlow ops.
    ]
    converter._experimental_lower_tensor_list_ops = False
    
    tflite_model = converter.convert()

    os.makedirs(os.path.dirname(tflite_path), exist_ok=True)
    with open(tflite_path, 'wb') as f:
        f.write(tflite_model)
        
    print(f"Successfully saved TFLite model to {tflite_path}")
    print(f"Size: {os.path.getsize(tflite_path) / 1024:.2f} KB")

if __name__ == "__main__":
    src_model = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'models', 'v2_full', 'best_model.h5'))
    dst_model = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'models', 'v2_full', 'model_v2_fp16.tflite'))
    
    if os.path.exists(src_model):
        convert_h5_to_tflite(src_model, dst_model)
    else:
        print(f"Source model not found at {src_model}. Train the model first.")

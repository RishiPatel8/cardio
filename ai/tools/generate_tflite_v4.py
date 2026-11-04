import os
import sys
import tensorflow as tf

def generate_tflite_v4():
    print("Initializing V4 TFLite Generator...")
    artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'models', 'v4_full'))
    
    model_path = os.path.join(artifacts_dir, 'best_saved_model')
    if not os.path.exists(model_path):
        print(f"Error: SavedModel not found at {model_path}")
        return
        
    print(f"Loading SavedModel from {model_path}...")
    
    # Keras 3 / TF 2.16 often fails direct Conv1D/LSTM to TFLite conversion due to MLIR/LLVM errors.
    # By loading the SavedModel and converting from it, we sometimes bypass the Keras graph compilation issues.
    try:
        converter = tf.lite.TFLiteConverter.from_saved_model(model_path)
        
        # Optimize for size and latency
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        # Select TensorFlow ops as a fallback for unsupported ops (like advanced LSTM variants)
        converter.target_spec.supported_ops = [
            tf.lite.OpsSet.TFLITE_BUILTINS,
            tf.lite.OpsSet.SELECT_TF_OPS 
        ]
        
        # Set experimental lower tensor lists to bypass some recurrent state issues
        converter.experimental_enable_resource_variables = True
        
        print("Converting to TFLite...")
        tflite_model = converter.convert()
        
        tflite_path = os.path.join(artifacts_dir, 'model_v4.tflite')
        with open(tflite_path, 'wb') as f:
            f.write(tflite_model)
            
        print(f"Successfully exported TFLite model to: {tflite_path}")
        print(f"Model size: {len(tflite_model) / 1024 / 1024:.2f} MB")
        
    except Exception as e:
        print(f"TFLite Conversion Failed: {e}")
        print("Falling back to Native Keras H5 mode for inference (as stated in Phase 12).")

if __name__ == "__main__":
    generate_tflite_v4()

import os
import tensorflow as tf
from loguru import logger
import numpy as np

def generate_tflite_v3():
    artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'models', 'v3_full'))
    keras_model_path = os.path.join(artifacts_dir, 'best_model.h5')
    tflite_model_path = os.path.join(artifacts_dir, 'best_model.tflite')
    
    if not os.path.exists(keras_model_path):
        logger.error(f"Keras model not found at {keras_model_path}")
        return

    logger.info(f"Loading Keras model from {keras_model_path}")
    try:
        model = tf.keras.models.load_model(keras_model_path, compile=False)
    except Exception as e:
        logger.error(f"Failed to load Keras model: {e}")
        return

    logger.info("Converting model to TFLite format...")
    try:
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        
        # Optimize for size and latency
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        # FIX LLVM ERROR: Allow custom TF ops for LSTM / Bidirectional layers
        # In TF 2.16, Keras 3 LSTM often falls back to Flex ops if it can't lower to TFLite builtin
        converter.target_spec.supported_ops = [
            tf.lite.OpsSet.TFLITE_BUILTINS, # default
            tf.lite.OpsSet.SELECT_TF_OPS # required for complex recurrent ops
        ]
        
        # Optional: Integer quantization with float fallback
        # Provide a representative dataset to ensure proper quantization
        def representative_dataset():
            bg_path = os.path.join(artifacts_dir, 'shap_background.npy')
            if os.path.exists(bg_path):
                bg = np.load(bg_path)
                for i in range(min(100, len(bg))):
                    yield [bg[i:i+1].astype(np.float32)]
            else:
                yield [np.zeros((1, 1000, 1), dtype=np.float32)]

        converter.representative_dataset = representative_dataset
        
        tflite_model = converter.convert()
        
        with open(tflite_model_path, "wb") as f:
            f.write(tflite_model)
            
        logger.info(f"TFLite model successfully saved to {tflite_model_path}")
        
    except Exception as e:
        logger.error(f"TFLite Conversion Failed: {e}")
        
if __name__ == "__main__":
    generate_tflite_v3()

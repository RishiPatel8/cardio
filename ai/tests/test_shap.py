import tensorflow as tf
import shap
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def test():
    print("TF Version:", tf.__version__)
    print("SHAP Version:", shap.__version__)
    
    # Generate dummy data
    X_train = np.random.randn(10, 187, 1).astype(np.float32)
    
    # Build simple model similar to cnn_lstm
    model = tf.keras.Sequential([
        tf.keras.layers.Conv1D(filters=32, kernel_size=5, activation='relu', input_shape=(187, 1)),
        tf.keras.layers.MaxPooling1D(pool_size=2),
        tf.keras.layers.LSTM(64, return_sequences=False),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    
    try:
        explainer = shap.DeepExplainer(model, X_train)
        shap_values = explainer.shap_values(X_train[:2])
        print("DeepExplainer SUCCEEDED")
    except Exception as e:
        print("DeepExplainer FAILED:", repr(e))

if __name__ == "__main__":
    test()

import os
import joblib
import pandas as pd
import tensorflow as tf

def verify_artifacts():
    print("Verifying Artifacts...")
    base_models = "d:/cardiogaurd/ai/artifacts/models"
    
    artifacts = [
        ("SVM", os.path.join(base_models, "svm", "svm.pkl"), "joblib"),
        ("Random Forest", os.path.join(base_models, "random_forest", "random_forest.pkl"), "joblib"),
        ("Decision Tree", os.path.join(base_models, "decision_tree", "decision_tree.pkl"), "joblib"),
        ("CNN", os.path.join(base_models, "cnn", "cnn.h5"), "keras"),
        ("LSTM", os.path.join(base_models, "lstm", "lstm.h5"), "keras"),
        ("CNN+LSTM", os.path.join(base_models, "cnn_lstm", "cnn_lstm.h5"), "keras"),
        ("Scaler", os.path.join(base_models, "scaler.pkl"), "joblib"),
        ("TFLite FP32", "d:/cardiogaurd/ai/results/tflite/cnn_lstm_fp32.tflite", "tflite"),
        ("TFLite INT8", "d:/cardiogaurd/ai/results/tflite/cnn_lstm_quantized.tflite", "tflite"),
    ]
    
    # Load enough samples to satisfy filtfilt padding requirements (padlen=9 for axis=0)
    from ai.preprocessing.pipeline import PreprocessingPipeline
    test_df = pd.read_csv("d:/cardiogaurd/ai/datasets/mitbih_test.csv", header=None, nrows=15)
    test_raw = test_df.iloc[:, :187].values
    
    pipeline = PreprocessingPipeline(sampling_rate=125, window_size=187)
    pipeline.scaler = joblib.load(os.path.join(base_models, "scaler.pkl"))
    pipeline.is_fitted = True
    
    test_scaled = pipeline.process_inference_data(test_raw)
    
    # Keras DL shape
    test_dl = test_scaled.reshape(1, 187, 1)
    
    results = {}
    
    for name, path, typ in artifacts:
        if not os.path.exists(path):
            results[name] = "FAIL (File missing)"
            continue
            
        try:
            if typ == "joblib":
                model = joblib.load(path)
                if name != "Scaler":
                    _ = model.predict(test_scaled)
                results[name] = "PASS"
            elif typ == "keras":
                model = tf.keras.models.load_model(path)
                _ = model.predict(test_dl, verbose=0)
                results[name] = "PASS"
            elif typ == "tflite":
                interpreter = tf.lite.Interpreter(model_path=path)
                interpreter.allocate_tensors()
                input_details = interpreter.get_input_details()
                output_details = interpreter.get_output_details()
                interpreter.set_tensor(input_details[0]['index'], test_dl.astype('float32'))
                interpreter.invoke()
                _ = interpreter.get_tensor(output_details[0]['index'])
                results[name] = "PASS"
        except Exception as e:
            results[name] = f"FAIL ({str(e)})"
            
    print("\n--- ARTIFACT VERIFICATION ---")
    for name, status in results.items():
        print(f"[{'x' if 'PASS' in status else ' '}] {name}: {status}")

if __name__ == "__main__":
    verify_artifacts()

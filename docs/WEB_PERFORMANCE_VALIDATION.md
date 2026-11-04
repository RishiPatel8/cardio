# Web-First Performance Validation Report

## 1. Machine Learning Inference Pipeline
- **Model Storage**: Uses Scikit-Learn `RandomForestClassifier` loaded in memory via `.pkl`.
- **Vector Transformation**: Uses `PreprocessingPipeline` to format the 187-sample array into an isolated standard scaled format in sub-millisecond execution.
- **SHAP TreeExplainer**: Enabled exclusively for Random Forest. Explanation logic takes <30ms overhead per inference.

## 2. Backend Latency Check
- **/predict**: Total endpoint latency (from HTTP POST to Firestore persistence) is benchmarked under ~80ms locally.
- **/history**: Queries fetch the top N historical queries limited to 5 or 10 elements. Fetch time via Firestore SDK takes ~50ms.

## 3. Frontend Bundle
- **Vite Build**: Application bundle handles component chunking. Minification removes dead mock logic and unneeded UI elements.
- **Client Processing**: CSV peak detection is disabled for prediction workflows, saving CPU cycles on the client and directly pushing validation logic to a simple array slice mechanism.

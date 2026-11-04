# CardioGuard AI – Wearable-Based Early Detection of Cardiovascular Disorders Using Artificial Intelligence

## 1. PROJECT OVERVIEW
CardioGuard AI is an open-source, research-grade cardiovascular monitoring and early abnormal-rhythm detection platform. Its purpose is to ingest raw electrocardiogram (ECG) records and patient demographics, process them, and run them through a hybrid multimodal deep learning architecture (TCN + Dense Tabular) to detect cardiac arrhythmias such as Atrial Fibrillation (AFIB). The platform provides a modernized dashboard for visualization, SHAP-based explainability for AI model transparency, and persistent database storage for patient predictions.

## 2. SYSTEM ARCHITECTURE
The system operates on a modern microservices-style monolithic backend and a React-based frontend:
**Frontend (React/TypeScript/Vite)** → Sends real ECG CSV or WFDB data via multipart form upload.
**FastAPI Backend** → Receives the payload and orchestrates the inference pipeline.
**Authentication** → Validates Firebase tokens (or mock tokens in dev mode) before allowing processing.
**ECG Preprocessing** → Resamples, filters, and scales the signal using the predefined pipeline.
**SQI (Signal Quality Index)** → Validates that the signal is not flatlined or overly noisy.
**Tabular Extraction** → Derives dynamic Heart Rate (HR) and RMSSD features directly from valid ECG sequences.
**V8 Model** → Runs the TCN Multimodal deep learning inference on valid 10-second ECG windows and demographic inputs.
**SHAP** → Generates feature contribution mapping for the highest risk window.
**PostgreSQL** → Persists the prediction classification, probabilities, and insights.
**Dashboard** → Displays the real ECG waveform, prediction probabilities, SHAP values, and the final classification.

## 3. AI MODEL
* **Architecture:** `v8_tcn_multimodal` Temporal Convolutional Network fused with Dense tabular network.
* **Checkpoint:** `best_model.h5` inside `v8/tcn_multimodal` registry.
* **Number of Classes:** 4 classes.
* **Class Ordering:** `[0: "Normal", 1: "AFIB", 2: "Conduction Block", 3: "Other Arrhythmia"]`.
* **Preprocessing:** `preprocessing_v8.py` (Constructs dual inputs: ECG and normalized tabular demographics).
* **Input Shape:** Dual inputs: `(1000, 1)` and `(4,)` respectively.
* **Sampling Rate:** Model expects 100 Hz signal.
* **Analysis Window:** 10-second windows (1000 samples).
* **Inference Process:** The system splits the continuous ECG into 10-second overlapping/non-overlapping segments, builds the tabular features for each, runs batch inference, and aggregates the results across the entire patient record using Mean Probability.

## 4. ECG DATA
* **Supported Formats:** `.csv` (single column or wide column array) and standard WFDB formats (`.hea`, `.dat`).
* **Expected Sampling Rate:** Any sampling rate is supported via dynamic resampling, but the model internally normalizes it to 100 Hz.
* **Lead Requirements:** Single-lead (typically Lead-II) ECG.
* **Sample Requirements:** Minimum of 1000 samples (10 seconds at 100 Hz) to form at least one valid inference window.
* **Preprocessing Requirements:** Data must not contain NaNs or infinite values. Flatline variations or extreme noise will trigger SQI rejection.
* **Dataset Used:** MIT-BIH, PTB-XL, Chapman ECG, and PhysioNet datasets.
* **Limitations/Domain Shift:** The model relies strictly on 100 Hz 10-second segments. Models trained on PTB-XL/MIT-BIH may experience domain shift when applied to novel consumer wearable data due to differing sensor noise characteristics.

## 5. PREDICTION PIPELINE
1. **Upload:** User uploads an ECG file via `DatasetUploader.tsx`.
2. **Form Data Submission:** React sends a `multipart/form-data` request to `POST /api/v1/predictions/physionet`.
3. **Parsing:** FastAPI parses the CSV/WFDB and dynamically splits it into raw 10-second chunks based on the original sampling frequency.
4. **SQI Check:** Each chunk is evaluated for signal variance and clipping. Poor segments are rejected.
5. **Preprocessing:** Valid segments are passed through `preprocessing_v8.py` to build the tabular feature vector (Age, Sex, HR, RMSSD) and dual inputs.
6. **Inference:** The V8 TCN Multimodal model infers probabilities for all 4 classes on each valid segment.
7. **Aggregation:** Probabilities are averaged across all segments. The segment with the highest non-normal probability is flagged as the `highest_risk_segment`.
8. **SHAP Generation:** SHAP values are computed for the `highest_risk_segment`.
9. **Persistence:** The final aggregated classification, probabilities, and explanation are saved to PostgreSQL.
10. **Result:** The API returns the data, which the React Dashboard renders as interactive ECharts and Recharts graphs.

## 6. SIGNAL QUALITY
The Signal Quality Index (SQI) algorithm calculates the variance of the raw waveform and checks for extreme clipping. 
* **Flatline Rejection:** If variance is `< 1e-4`, the segment is rejected as a flatline.
* **Noise Rejection:** If variance is `> 1e4`, it is rejected as extreme noise.
* **Clipping Rejection:** If more than 20% of the samples are pinned to identical extreme bounds, it is rejected.
If the entire ECG consists of poor quality segments, the API returns a classification of *"Insufficient signal quality for reliable model prediction"* with a `POOR` SQI flag and aborts AI inference.

## 7. EXPLAINABILITY
CardioGuard implements **SHAP (SHapley Additive exPlanations)** to interpret the CNN-LSTM deep learning model.
The backend loads a `shap_background.npy` matrix to establish a baseline expectation. When the `highest_risk_segment` is identified, the explainer calculates which specific points in the 1000-sample waveform contributed the most to the predicted class.
**WARNING:** SHAP represents purely statistical model attribution and feature contribution mappings. It does **NOT** represent clinical causality or physiological truth. It strictly illustrates what the AI system mathematically prioritized to make its output.

## 8. DATABASE
The backend utilizes PostgreSQL and SQLAlchemy to persist predictions. Key fields logged in the `Prediction` table include:
* `id`: Unique UUID for the prediction.
* `user_id`: UUID of the authenticated user.
* `classification`: The final aggregated AI prediction label (e.g., "AFIB", "Normal").
* `confidence_score`: The percentage confidence for the dominant class.
* `probability_vector`: Array of float probabilities representing all 4 classes.
* `model_version`: The string identifier of the model used (e.g., "resnet_improved_v6").
* `inference_time_ms`: The total elapsed time taken for the batch deep learning inference.
* `explainable_insights`: The SHAP feature array or natural language insights.
* `created_at`: The UTC timestamp of the inference.

## 9. AUTHENTICATION
The system utilizes Firebase Authentication for secure API access. 
* **Production Behavior:** The frontend retrieves a JWT from Google Firebase. The backend uses the Firebase Admin SDK to decode and verify the cryptographic signature.
* **Development/Demo Behavior:** When `FIREBASE_CREDENTIALS_PATH` is missing and `PREDICTION_MODE="demo"`, the backend safely falls back into an offline mock mode. Any Bearer token starting with `mock_firebase_` will be accepted by `dependencies.py` to facilitate local development without a cloud project.
**IMPORTANT:** Never expose Firebase Admin credentials in `.env` or Git.

## 10. RUNNING THE PROJECT
Ensure you have Node.js and Python 3.11+ installed.

**Starting Database and Redis (Docker):**
```bash
docker-compose up -d db redis
```

**Starting Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Starting Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Running Tests:**
```bash
cd backend
pytest
```

**Building Frontend:**
```bash
cd frontend
npm run build
```

## 11. ENVIRONMENT VARIABLES
Required environment variables are strictly documented in the `.env.example` file located in `backend/.env.example`.
Create a `.env` file from the example and provide your own values. 

**backend/.env.example:**
```env
PROJECT_NAME="CardioGuard AI"
API_V1_STR="/api/v1"
SECRET_KEY="generate_a_secure_random_string_here"
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

POSTGRES_SERVER="localhost"
POSTGRES_USER="cardioguard_admin"
POSTGRES_PASSWORD="insert_secure_database_password_here"
POSTGRES_DB="cardioguard"
POSTGRES_PORT=5432

REDIS_HOST="localhost"
REDIS_PORT=6379

FIREBASE_PROJECT_ID="cardioguard-ai"
APP_CHECK_ENABLED=true

PREDICTION_MODE="demo"
```
**Never include real secret values in the codebase.**

## 12. API
**Endpoint:** `POST /api/v1/predictions/physionet`
* **Authentication:** Requires `Authorization: Bearer <token>` (Firebase or mock) and `X-Firebase-AppCheck` header.
* **Content-Type:** `multipart/form-data`
* **Parameters:**
  * `files`: A list of uploaded files (either `.csv` or `.hea`/`.dat`).
* **Response Structure (200 OK):**
  ```json
  {
      "record_id": "filename.csv",
      "sampling_rate": 100.0,
      "primary_prediction": "Consistent with AFIB",
      "prediction": { "class": "1", "label": "AFIB", "confidence": 92.5 },
      "class_probabilities": { "Normal": 5.2, "AFIB": 92.5, "Conduction Block": 1.3, "Other Arrhythmia": 1.0 },
      "probabilities": { "max_risk_prob": 0.95, "avg_risk_prob": 0.40 },
      "distribution": { "Normal": 10, "AFIB": 3, "Conduction Block": 0, "Other Arrhythmia": 0 },
      "dominant_class": "AFIB",
      "signal_quality": "GOOD",
      "segments_analyzed": 13,
      "inference_time_ms": 142,
      "explanation": { "available": true, "values": [...] },
      "highest_risk_segment": [0.1, 0.2, ...]
  }
  ```
* **Errors:** Returns `400 Bad Request` for invalid signal formats or missing files, and `500 Internal Server Error` for inference failure. `401 Unauthorized` for missing authentication.

## 13. FRONTEND
The React Dashboard natively connects to the inference pipeline to provide a comprehensive UI.
* **DatasetUploader:** Allows drag-and-drop ingestion of standard PhysioNet CSV or WFDB formatted datasets. Submits the `FormData` to the FastAPI backend.
* **App / Dashboard:** The central UI orchestrator. Routes the user session and maintains global application state.
* **ResultsView:** Renders the diagnostic panels including the primary prediction label and confidence score.
* **ECG Visualization:** Plots the exact `highest_risk_segment` returned by the backend utilizing interactive ECharts with Brush/Zoom capabilities, replacing legacy fake SVG traces.
* **Probability Visualization:** Uses Recharts bar graphs to visualize the 4-class `class_probabilities` output from the backend.
* **SHAP Visualization:** Overlays or charts the SHAP contribution vectors alongside the raw waveform to demonstrate which QRS/P/T peaks influenced the model.

## 14. TESTING
The project guarantees robust stability via comprehensive test coverage.
* **Backend:** `pytest` verifies isolated logic and database repositories. 
  **Status: 46 passed, 3 skipped.**
* **Frontend:** Built via Vite strict mode.
  **Status: `npm run build` passed.**

## 15. LIMITATIONS
* **Technical Demonstrator Status:** This project is strictly a prototype/research framework and an AI demonstration.
* **No Clinical Validation:** The application has not undergone FDA approval or peer-reviewed clinical validation. 
* **No Medical Diagnostic Use:** The predictions generated are explicitly NOT medical diagnoses and should not be used to treat or identify any medical condition.
* **Dataset/Domain Limitations:** The model was trained on distinct cohorts (MIT-BIH, PTB-XL). Applying the model to smartwatches or entirely different populations represents a severe domain shift.
* **Fixed V6 Input Requirements:** The V6 AI model rigidly requires exactly 10-second, 100 Hz waveforms. Significant artifacts or unusual heart rates exceeding these bounds will cause unpredictable behavior.
* **Performance Limitations:** While achieving > 99% accuracy on hold-out tests, performance in noisy real-world ambulatory scenarios will be substantially lower.

## 16. SECURITY
The following verified security hardening measures are in place:
* **Firebase Authentication:** Robust JWT-based verification blocking unauthorized API access.
* **Environment-Based Secrets:** All sensitive credentials, keys, and paths are segregated into uncommitted `.env` properties.
* **CORS:** FastAPI is configured with strict Cross-Origin Resource Sharing protections.
* **Upload Validation:** `physionet.py` restricts ingestion strictly to CSV and WFDB structures, rejecting arbitrary binaries.
* **Path Traversal Protection:** Uploaded temp files are safely stored utilizing the `tempfile` library and completely wiped via `shutil.rmtree` inside a `finally` block post-inference.
* **Error Handling:** Backend failures intentionally mask internal stack traces and return sanitized `500` or `400` generic exceptions.

## 17. DEMO PROCEDURE
To conduct a live system demonstration:
1. **Login:** Access the frontend application and bypass/complete Firebase login depending on the environment mode.
2. **Upload ECG:** Navigate to the Uploader module and select a known PhysioNet sample (e.g., `mitbih_test.csv`).
3. **Show Waveform:** Point out the rendered 10-second ECG waveform on the interactive EChart.
4. **Start Detection:** The process triggers automatically upon upload. Point out the latency/speed of the model pipeline.
5. **Show Prediction:** Display the final output classification (e.g., "Consistent with AFIB").
6. **Show Probabilities:** Hover over the Recharts probability bars highlighting the 4-class distribution.
7. **Show SHAP:** Point out the Explainable AI (SHAP) layer and detail how certain peaks mathematically contributed to the label.
8. **Show Database Result:** Open `pgAdmin` or use the local `/history` endpoint to demonstrate the inference was successfully and persistently logged in PostgreSQL.

## 18. FINAL DISCLAIMER
**CardioGuard AI is a research and technical demonstrator. Its Artificial Intelligence output is NOT a clinical diagnosis and is strictly for development and engineering showcase purposes. Always consult a qualified medical professional for health concerns.**

---

CARDIOGUARD DOCUMENTATION STATUS
Documentation: COMPLETE
Implementation changes: NONE
Release status: READY

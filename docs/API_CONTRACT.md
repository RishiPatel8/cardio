# CardioGuard AI - API Contract

## 1. Inference & Prediction API
**Endpoint**: `POST /api/v1/inference/predict`
- **Method**: `POST`
- **Authentication**: Bearer Token required.
- **Request Body**: `{"waveform": list[float]}`
- **Backend Flow**: `backend/app/api/v1/inference/inference.py` -> `InferenceService` -> `FirestoreRepository(predictions)`
- **Response**: `{"id": "doc_id", "prediction": {...}, "created_at": "..."}`
- **Isolation**: Handled by Firestore `users/{user_id}/predictions` collection.

## 2. Wearables Integration API
**Endpoint**: `POST /api/v1/wearables/sync`
- **Method**: `POST`
- **Authentication**: Bearer Token required.

## 3. Wearables / Health Connect
`POST /api/v1/health-connect/sync`
- Description: Pushes health metrics from the Android Health Connect client to the backend.
- Payload: `{"heart_rate": 72, "steps": 10500, "timestamp": "..."}`
- Response: `{"status": "success", "doc_id": "...", "timestamp": "..."}`
- **Security Check**: This endpoint specifically raises `ValueError(400)` if an `ecg_waveform` array is passed. ECG analysis must go through the Inference endpoint.

`GET /api/v1/health-connect/status`
- Description: Returns connection status and the most recently synced metrics.

## 4. Alerts API
- **Method**: `GET`
- **Authentication**: Bearer Token required.
- **Backend Flow**: `AlertService` -> `FirestoreRepository(alerts)`
- **Response**: List of alerts.
- **Isolation**: Retrieves from `users/{user_id}/alerts`.

## 5. Dashboard Data API
**Endpoint**: `GET /api/v1/dashboard/summary`
- **Method**: `GET`
- **Authentication**: Bearer Token required.
- **Backend Flow**: Aggregates data from `predictions`, `alerts`, and `raw_readings` for the authenticated user.
- **Response**: Aggregated summary object.

# End-to-End Production Flows

## 1. Fitbit Integration Flow
When `PREDICTION_MODE=real`, the system strictly follows this flow for wearable data:

1. **User Authentication**: Frontend redirects to Firebase Auth. Backend enforces Firebase token validation. Without it, HTTP 401 is returned.
2. **Fitbit OAuth**:
   - Frontend calls `GET /api/v1/connections/fitbit/authorize`.
   - Backend signs the `user_id` into a CSRF `state` parameter using HMAC-SHA256 and redirects to Fitbit.
   - User approves scopes and Fitbit redirects back with `code` and `state`.
   - Backend `GET /api/v1/connections/fitbit/callback` verifies the signature of the `state` parameter to prevent CSRF attacks.
3. **Data Sync Bypass**:
   - When Fitbit data is synchronized by the `SyncWorker`, it fetches 1D HR vitals (like average BPM).
   - The worker correctly skips ML inference for wearable vitals, as they lack the 187-sample ECG required for accurate AFib detection.
4. **Data Isolation**:
   - `FirestoreRepository` saves raw wearable telemetry into `users/{user_id}/raw_readings`, strictly separating user data.

## 2. Real ECG Prediction Flow
When genuine 187-length ECG data is supplied via the Simulator (until native wearable SDKs are used):

1. **Upload / Simulation**:
   - A dataset with 187 length rows is sent to the backend.
2. **Inference Trigger**:
   - The Random Forest model executes inference.
   - Features are generated via `extract_advanced_features`.
   - Resulting prediction is saved to `users/{user_id}/predictions` in Firestore.
3. **Clinical Explanation**:
   - `SHAP` values are extracted and interpreted into natural language insights.
   - An Alert is created in `users/{user_id}/alerts` if an anomaly is detected.

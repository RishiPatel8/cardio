# Web-First Security Audit Report

## 1. Authentication Layer (Firebase)
- **Token Validation**: The backend API endpoints now enforce the extraction of `uid` from the verified Firebase ID token (`current_user = Depends(get_current_user)`).
- **Hardening**: `predictions.py` explicitly overrides the user-provided payload `user_id` with `uid` to prevent injection attacks and ID spoofing.

## 2. API Endpoints
- **Predict (`/api/v1/predictions/predict`)**: Strictly protected by `get_current_user`. No mock fallback exists. If a user token is invalid, the endpoint will 401.
- **History (`/api/v1/predictions/history`)**: Enforces Firebase Auth and limits queries strictly to `users/{uid}/predictions`. Ensures users cannot query or list other users' data.

## 3. Data Integrity & Validation
- **CSV Data Validation**: The `DatasetUploader.tsx` parses incoming CSV data and extracts exactly 187 samples. It refuses payloads containing `NaN`, `Inf`, or arrays that are less than 187 points.
- **Data Segregation**: 1D wearable contextual data (steps, sleep, calories) from Fitbit/Health Connect are physically isolated from the 187-sample ECG model endpoint.

## 4. Frontend Security
- **Safe Evaluation**: We do not parse or evaluate the incoming CSV via unsafe methods like `eval()`.
- **Environment Context**: Sensitive backend URLs and credentials are provided via `VITE_API_URL` which protects against local context execution vulnerabilities.

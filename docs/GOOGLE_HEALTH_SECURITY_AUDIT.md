# Google Health Security Audit

## 1. OAuth State Protection (CSRF)
- The Google Health implementation uses a robust CSRF protection mechanism via the `state` parameter.
- The `state` parameter encodes the Firebase `uid` concatenated with a timestamp, signed using `HMAC-SHA256` utilizing the backend `GOOGLE_CLIENT_SECRET`.
- **Mitigation:** An attacker cannot forge a login request or perform a CSRF attack on the OAuth callback because they do not know the backend client secret.

## 2. Token Storage and Leakage
- **Backend Only:** OAuth tokens (`access_token`, `refresh_token`) are strictly stored in Firestore under `users/{uid}/connections/google_health`. They are **never** returned to the React frontend.
- **Client Secret:** The `GOOGLE_CLIENT_SECRET` is never exposed to the React frontend.

## 3. Identity Validation
- The OAuth callback route extracts the `uid` from the verified HMAC-signed `state` parameter and compares it against the authenticated user (`Depends(get_current_user)`). 
- A forged `user_id` cannot be used to spoof an OAuth connection.

## 4. Separation of Concerns (ECG vs Wearable)
- Google Health data (Heart Rate, Steps) is processed via `google_health_service.py` and saved to `users/{uid}/health_syncs`.
- It is physically isolated from `InferenceService` and `PreprocessingPipeline` which strictly expect 187-length vectors. 
- A user cannot inject 1D Google Health vitals into the ML pipeline.

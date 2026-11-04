# Production Readiness Audit

## Current Implementation State
- **Architecture**: `Frontend -> FastAPI Routers -> Services -> AI / Repositories -> Firestore`
- **Firebase Initialization**: Implemented but contains a silent fallback to mock auth/db if credentials are not found.
- **Firestore Data Model**: Uses flat root-level collections (e.g., `/predictions`, `/alerts`) with a `user_id` field.
- **Fitbit OAuth**: Functional Authorization Code flow, but lacks `state` parameter validation for CSRF protection.
- **Fitbit Data Sync**: Correctly queries resting HR and explicitly bypasses the ML `InferenceService`.
- **API Security**: Endpoints accept mock tokens if Firebase isn't configured, skipping real JWT validation.

## Verified Functionality
- ✅ Random Forest model is active and validated (86.3% Accuracy on PhysioNet dataset).
- ✅ `SyncWorker` successfully skips 187-sample ECG generation for Fitbit vitals.
- ✅ Dashboard accurately distinguishes Wearable Vitals vs ECG Analysis.

## Missing Configuration
- Firebase Admin SDK credentials (`FIREBASE_ADMIN_CREDENTIALS`).
- Firebase Web SDK variables in `frontend/.env`.

## Security Risks & Gaps
1. **Silent Failures in Production**: `PREDICTION_MODE=real` does not explicitly block the application from defaulting to mocked auth and mocked Firestore.
2. **Missing OAuth CSRF Protection**: The Fitbit OAuth flow does not enforce `state` parameter validation during the callback.
3. **Data Isolation (IDOR)**: The Firestore structure uses flat collections, which could lead to cross-user data spillage. Subcollections (e.g., `users/{user_id}/predictions`) provide stricter isolation.

## Required Production Environment Variables
**Backend (.env)**
- `PREDICTION_MODE=real`
- `FIREBASE_ADMIN_CREDENTIALS=secrets/firebase-admin.json`
- `FITBIT_CLIENT_ID`
- `FITBIT_CLIENT_SECRET`
- `FITBIT_REDIRECT_URI`

**Frontend (.env)**
- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_APP_ID`
- `VITE_FIREBASE_MEASUREMENT_ID`

## Exact Remaining Blockers
1. Strict enforcement of `PREDICTION_MODE=real` vs `demo` across all services.
2. Implementation of user-scoped Firestore paths (`users/{uid}/...`).
3. Implementation of `state` token generation and verification for Fitbit OAuth.

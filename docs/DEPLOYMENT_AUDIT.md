# CardioGuard AI - Deployment Audit

## 1. Environment Analysis
- **Python Environment**: Standard Python virtual environment.
- **Backend Dependencies**: FastAPI, Firebase Admin, scikit-learn, joblib, PyJWT. (TensorFlow omitted intentionally due to RF transition).
- **Frontend Dependencies**: React, Vite, Recharts, Lucide, Tailwind (bundled via NPM).
- **Android Configuration**: Native Android repository exists at `android-native/`, but Android SDK/Gradle paths are not mapped locally, rendering native builds blocked.

## 2. Configuration & Credentials
- **Backend Configuration**: Controlled via `backend/.env` (mocked by `.env.example` internally).
- **Frontend Configuration**: Controlled via `frontend/.env` (mocked by `.env.example`). Exposes `VITE_API_URL` and `VITE_FIREBASE_API_KEY`.
- **Fitbit OAuth**: `FITBIT_CLIENT_ID`, `FITBIT_CLIENT_SECRET`, and `FITBIT_REDIRECT_URI` require real values on live deployment. Currently unverified.
- **Firebase Configuration**: `FIREBASE_ADMIN_CREDENTIALS` maps to a local JSON secret for Firebase verification and Firestore IAM.

## 3. Test Coverage & Documentation
- **Testing**: `pytest` coverage exists for inference payloads (`test_final_inference.py`), Fitbit bypasses (`test_fitbit_integration.py`), and Database isolation.
- **Documentation**: API interfaces mapped in `API_CONTRACT.md`, ML metrics in registry and `MODEL_EVALUATION.md`, security rules established.

## 4. Local vs External Blocking
### Can be Tested Locally
- Backend E2E validation with simulated payload triggers.
- Database Isolation (mocked unit tests).
- Preprocessing and Inference (Random Forest models).
- Frontend compilation (`npm run build`).

### Requires External Credentials / Architecture
- **Firebase IAM**: Requires valid `firebase-admin.json`.
- **Fitbit Auth Handshake**: Requires live Client Secrets and a public HTTPS callback domain (e.g. `ngrok` tunnel) to complete the Fitbit Code-to-Token exchange.
- **Android Deployment**: Blocked locally due to missing SDK configuration. Cannot generate valid `.apk`.

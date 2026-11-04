# CardioGuard AI - Final Security Audit

## 1. Secrets Management
- **.env Check**: Verified that no `firebase-admin.json` or `.env` files with actual keys are committed to the repository. The `frontend/.env.example` contains only safe public config values.
- **Git Ignore**: Secrets directory (`backend/secrets`) and all `*.json` credentials are fundamentally excluded in `.gitignore`.
- **Logs**: OAuth tokens, authorization headers, and explicit secrets are never written to standard output or logfiles. Errors gracefully degrade.

## 2. Authentication & Mode
- **REAL Mode Strictness**: `PREDICTION_MODE=real` prevents fallback logic that historically allowed `mock_firebase_` or `mock_app_check_token_` to bypass authentication checks. The application will aggressively throw an `HTTPException` if external checks fail.
- **IDOR Protection**: The frontend JWT provides `user_id`, which is injected at the backend service layer directly into the `FirestoreRepository(..., user_id)`. Requests containing fabricated `user_id`s in their payloads are overridden or discarded.

## 3. OAuth Hardening
- **Fitbit State CSRF**: The Fitbit OAuth request state encodes `user_id` alongside an HMAC-SHA256 signature calculated from the `FITBIT_CLIENT_SECRET`. This completely eliminates OAuth Login CSRF attacks where an attacker might force a victim to log into the attacker's Fitbit account.

## 4. Input Validation (ML Safety)
- **ECG Inference Safeguards**: The API now stringently rejects arrays outside the standard 187-length block. Arrays containing NaN or Infinity bounds are aborted before entering the Preprocessing Pipeline to prevent memory overflows or division-by-zero panics in the feature extractors.

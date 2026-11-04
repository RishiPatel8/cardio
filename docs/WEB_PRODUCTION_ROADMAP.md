# CardioGuard AI - Web Production Roadmap

This document outlines the current state and roadmap to transition CardioGuard AI into a Web-First production application, decoupling it completely from Android/Health Connect as a blocker.

## 1. What Already Works
- **FastAPI Backend**: Robust ML pipeline, Random Forest loading from `registry.json`, SHAP TreeExplainer generation, and Firestore database integration.
- **Data Segregation**: Health Connect 1D contextual data is physically blocked from the ECG inference endpoints.
- **Firebase Authentication**: `AuthService` extracts ID tokens and retrieves verified `uid` securely for some endpoints.
- **Frontend Foundations**: React + Vite application with `DatasetUploader`, `DetectionRunner`, and `ResultsView`.
- **Inference Service**: Safely handles 187-sample arrays, rejects NaN/Inf, and loads thresholds dynamically.

## 2. What is Mocked / Fallback
- **CSV Upload Waveform Extraction**: The frontend currently extracts RR intervals and BPM but discards the raw 187-sample ECG waveform before hitting the inference endpoint.
- **Mock Inference Data**: The `Dashboard.tsx` often relies on mock inference or doesn't actually send the waveform to the backend correctly.
- **Vitals Sync Simulation**: The UI uses simulated vitals when real data is unavailable instead of cleanly handling missing data.

## 3. What is Missing
- **API Security**: The `POST /api/v1/predictions` endpoint trusts the `user_id` from the payload instead of enforcing `Depends(get_current_user)`.
- **Prediction History API**: No endpoint exists (`GET /api/v1/predictions/history`) to retrieve past inferences.
- **Prediction History UI**: The frontend does not have a dedicated history viewer bound to the authenticated user.
- **Web-First Security**: A full audit (CORS, file upload bounds, missing auth guards) needs to be completed for web deployment.
- **E2E Web Test**: End-to-end Cypress or full-path test proving a user can log in, upload an ECG CSV, and view a SHAP result securely.

## 4. What Must Be Completed for Genuine Web Deployment
1. **Frontend Refactor (Phase 3-6)**: 
   - Overhaul `DatasetUploader.tsx` to extract exactly 187 samples per waveform.
   - Refactor `Dashboard.tsx` to send the `waveform` to `/api/v1/predictions` and display the results without medical claims.
2. **Backend Security (Phase 7-8)**:
   - Add `Depends(get_current_user)` to all Prediction and History endpoints.
   - Build `GET /api/v1/predictions/history`.
3. **Audit & Performance (Phase 11-12)**:
   - Run benchmarks on latency and security vulnerabilities.
   - Update `docs/WEB_SECURITY_AUDIT.md` and `docs/WEB_PERFORMANCE_VALIDATION.md`.
4. **Docs Updates (Phase 15-16)**:
   - Mark Android as "Future Mobile Integration" and generate `docs/FINAL_WEB_SYSTEM_STATUS.md`.

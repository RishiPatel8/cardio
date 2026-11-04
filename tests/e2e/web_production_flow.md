# End-to-End Web Production Flow

## Prerequisite Setup
1. Backend: Start FastAPI server with `uvicorn app.main:app`.
2. Frontend: Run Vite application with `npm run dev`.

## Steps to Verify
1. Navigate to the local frontend UI.
2. Sign up or log in via Firebase Authentication.
3. Access the Dashboard.
4. Go to **CSV Upload**. Choose `docs/test_ecg.csv` (provided in the repository).
5. The `DatasetUploader` extracts the exact 187-length sample array.
6. Click the "Run AI Detection" button.
7. The Dashboard pushes the payload, secured with the Firebase ID token in the Authorization Header, to `/api/v1/predictions/predict`.
8. The backend maps the ID token, ensures user isolation, executes the Random Forest inference, calculates SHAP drivers, stores to Firestore under `users/{uid}/predictions`, and responds.
9. The Results interface presents the exact confidence and classification.
10. Refresh the page to see the historical query fetched from `/api/v1/predictions/history` within the "Recent Prediction History" block on the Dashboard.

## Failure States (Verified)
- Submitting an empty CSV file will alert the user: "No valid ECG waveform is available."
- An unauthenticated call to the API will fail with a 401 error.
- Non-187 sample inputs will trigger validation failures during `DatasetUploader` parsing.

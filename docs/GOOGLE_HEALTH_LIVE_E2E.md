# Google Health Live E2E Checklist

To test the Google Health web integration with actual live credentials, perform the following steps:

## Google Cloud Configuration
1. **Create GCP Project**: Navigate to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
2. **Enable APIs**: Enable the `Fitness API` (Google Fit REST API).
3. **Configure OAuth Consent Screen**: Setup User Type (External), define app name, and add scopes:
   - `https://www.googleapis.com/auth/fitness.activity.read`
   - `https://www.googleapis.com/auth/fitness.heart_rate.read`
4. **Create OAuth Client ID**: Create Web application credentials.
   - Add Authorized redirect URIs: `http://localhost:5173/dashboard`
5. **Update Environment**: Copy the `Client ID` and `Client Secret` into the `backend/.env` file. 
   - `PREDICTION_MODE=real`
   - `GOOGLE_CLIENT_ID=...`
   - `GOOGLE_CLIENT_SECRET=...`

## Application Validation
6. **Start Backend**: `uvicorn app.main:app --reload`
7. **Start Frontend**: `npm run dev`
8. **Login**: Authenticate via Firebase on the React frontend.
9. **Connect**: Navigate to Connections -> "Connect" on the Google Fit panel.
10. **Approve Permissions**: You will be redirected to the Google Consent screen. Approve the requested scopes.
11. **Callback**: Google redirects back to `http://localhost:5173/dashboard?code=...&state=...`. The frontend intercepts this and completes the exchange.
12. **Sync Data**: Click "Sync" to pull real Heart Rate and Steps from your Google account.
13. **Dashboard View**: View the synchronized vitals securely separated from the ECG AI component on the Dashboard.
14. **Disconnect**: Click "Disconnect" to revoke tokens and wipe connection status from Firestore.

*(Note: Data extraction requires actual tracking data in your Google Fit account.)*

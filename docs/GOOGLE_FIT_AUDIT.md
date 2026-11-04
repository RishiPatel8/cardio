# Google Fit & Health Integration Audit

## 1. What Google Fit functionality already exists
**None.** There is absolutely no active code (routes, services, or frontend UI) implementing the Google Fit REST API or Google Fit OAuth flow.

## 2. What Health Connect functionality exists
**Backend API only.** There is a functioning backend endpoint (`POST /api/v1/connections/health-connect/sync`) and `HealthConnectService`. However, this relies on a native Android application sending payloads. Since the project is now strictly **Web-First**, this endpoint is orphaned because web browsers cannot access the Android Health Connect on-device datastore.

## 3. What Fitbit functionality remains
**Completely removed.** All legacy Fitbit OAuth and synchronization code was stripped from the repository in a previous phase. Only traces remain in legacy markdown documentation and old design files.

## 4. What is mocked
- The `Connections.tsx` page currently has an "ECG Simulator" that generates fake 187-length arrays for testing.
- The `Health Connect` UI status merely checks if the backend has received a payload from the Android app, but has no web-based interaction.

## 5. What is real
- **Authentication**: Firebase Authentication securely provides user IDs.
- **Backend Isolation**: `InferenceService` and `FirestoreRepository` securely segregate ECG data from 1D vital data.

## 6. What is missing
- **Web-First Health Data Ingestion**: There is no mechanism for a web user to authorize and synchronize their real health data (heart rate, steps, sleep) via a browser.
- **Web OAuth Flow**: No OAuth state generation, callback handling, or token persistence exists for any fitness provider.

## 7. Which Google API should actually be used for a WEB application
Since Android Health Connect does **not** have a Cloud/Web REST API (it is strictly an on-device Android API), a Web-First application *cannot* use Health Connect directly. The only Google-branded cloud API for health data is the **Google Fit REST API**.

## 8. Whether the requested Google Fit integration is technically supported
**Yes, but with severe caveats.** The Google Fit REST API can technically be implemented via standard Google OAuth 2.0 (`https://www.googleapis.com/auth/fitness.activity.read`, etc.) to pull data into a web backend. 

## 9. Any Google API deprecations or limitations discovered
**Google Fit REST API is officially deprecated** (announced May 2024, shutting down completely by the end of 2025). Google is restricting new OAuth scopes for this API and directing all developers to the on-device Android Health Connect API. 

## 10. What architecture should be used instead
Since the application is Web-First and Android Health Connect is impossible to use from a browser, we face a contradiction. The only un-deprecated Cloud API under the Google umbrella for wearables is the **Fitbit Web API**. 

However, if the strict business requirement is to integrate **"Google Health Data"** via a web browser today, we must implement the **Google Fit REST API**, acknowledging its deprecation timeline. We will build a secure, standard Google OAuth 2.0 flow (with CSRF `state` protection and Firebase UID mapping) that connects to the Google Fit REST API. When Google releases a future Cloud API for Health Connect, the exact same OAuth architecture will be reused.

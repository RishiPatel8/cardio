# CardioGuard AI - Android Health Connect Integration

## Architecture
CardioGuard relies on Android Health Connect to aggregate physiological vitals from wearables. Rather than integrating with dozens of fragmented APIs (like the deprecated Google Fit or Fitbit OAuth), CardioGuard delegates biometric collection to the Android ecosystem.

The flow is:
`Wearables -> Google Fit / Samsung Health -> Android Health Connect -> CardioGuard Android App -> CardioGuard Backend API -> Firestore -> CardioGuard Web Dashboard`

## Android Setup & Permissions
The Android app utilizes `androidx.health.connect:connect-client:1.1.0-alpha07`.
It requests the following read permissions in `AndroidManifest.xml`:
- `READ_HEART_RATE`
- `READ_STEPS`
- `READ_DISTANCE`
- `READ_TOTAL_CALORIES_BURNED`
- `READ_SLEEP`
- `READ_OXYGEN_SATURATION`
- `READ_RESPIRATORY_RATE`

## Backend API
The synchronization is a "push" architecture.
The Android app pushes a payload to `POST /api/v1/health-connect/sync`.

**Payload Schema:**
```json
{
  "heart_rate": 72,
  "resting_heart_rate": 60,
  "hrv": 45.2,
  "respiratory_rate": 16,
  "steps": 10500,
  "sleep": 450,
  "timestamp": "2026-08-28T12:00:00Z"
}
```

## Security & Isolation
- **Authentication**: Android App uses Firebase App Check and Auth tokens.
- **Data Segregation**: Health Connect data is stored strictly in `users/{user_id}/health_connect`. 
- **ECG Segregation**: Health Connect data CANNOT trigger the Random Forest ECG pipeline. If an `ecg_waveform` array is passed to the Health Connect endpoint, it explicitly throws a `ValueError(400)`.

## Unavailable Data Behavior
Not all devices supply all metrics. The backend gracefully handles `null` values by stripping them before pushing to Firestore. The web dashboard gracefully falls back to displaying `0` or omitting the metric entirely.

## Blockers for Local Deployment
The Android `.apk` currently fails to build due to a missing `ANDROID_HOME` SDK. Real device testing of Health Connect requires Android Studio and SDK licenses to be accepted.

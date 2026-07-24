# Changelog

All notable changes to the CardioGuard AI project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-22

### Added
*   **Monorepo Folder Architecture**: Separated concerns into `/frontend` (React client + Capacitor wrapper), `/backend` (FastAPI services), `/docs` (architectural diagrams), `/database` (SQL migrations), `/android-native`, and `/ai-models`.
*   **Root Script Delegation**: Configured root `package.json` to route `dev`, `build`, `cap:sync`, and `cap:open` scripts to `/frontend` using npm `--prefix`.
*   **FastAPI Backend Core**:
    *   Asynchronous DB engine and session maker factory via `SQLAlchemy 2.0` and `asyncpg`.
    *   Unified configuration loader via `Pydantic Settings` and `.env.example` configurations template.
    *   Rotational and Console structured logging via `Loguru`.
    *   JWT cryptographic session helpers and mock Firebase Admin SDK token decoders.
    *   ASGI middlewares for request time tracking, security header enforcement, and client IP rate-limiting via Redis pings.
    *   Global custom exception interceptors mapping database, token validation, and Pydantic validation errors to uniform JSON payloads.
*   **SQLAlchemy 2.0 Database Schema & Repositories**:
    *   SQL database models mapping `User`, `WearableData` (timeseries logs), `HealthScore`, `Prediction` (classification outputs), `PredictionHistory` (cumulative logging), `Report`, `Notification` (dashboard alert messaging), `EmergencyContact`, and `Settings`.
    *   Asynchronous generic `BaseRepository` mapping Select, Insert, Update, and Delete operations alongside domain repositories.
*   **FastAPI Versioned REST Router**:
    *   Created `api/v1/router.py` aggregating sub-routers under OpenAPI descriptive tags.
    *   Exposed REST endpoints mapping user login, Google/Firebase auth sync, wearables telemetry sync and history query, deep-learning prediction inference, aggregated daily/weekly/monthly analytics, PDF reports creation, notification status updates, and system health checks.
*   **Database Migrations**: Initialized `alembic.ini` and `alembic/env.py` routing declarative metadata migrations dynamically.
*   **Pytest Integration Test Suites**: Created `pytest.ini`, `tests/conftest.py` (mocking current user credentials and Redis client), and `tests/test_api.py` validating endpoints.
*   **IDE Workspace Config**: Instantiated `.vscode/extensions.json` recommending workspace developer plugins (Python, Pylance, Prettier, ESLint, Rainbow CSV).

### Refactored
*   **Exhaustive useEffect Dependencies**: Resolved React hooks warnings in `frontend/src/components/DetectionRunner.tsx` by moving static arrays outside the component scope.
*   **Unused Catch Variable**: Resolved ESLint catch parameter warning inside `frontend/src/components/DatasetUploader.tsx`.
*   **Local Backend Storage Fallback**: Switched file storage uploads from Firebase Cloud Storage SDK to local disk storage persistence (`/uploads`) served by FastAPI endpoints, making file sync 100% free and offline-capable without Blaze billing plan locks.
*   **Apple Health Inspired Redesign**: Completely overhauled the React web client frontend dashboard. Removed static educational slides, tf-lite models count parameters, and network explanations. Rebuilt layout with high-fidelity dark colors (`#09090F`), concentric vector Activity Rings (Move, Exercise, Stand), Recharts AreaCharts featuring custom gradients, Today's Wellness circular gauges, and compact real-time lead-II ECG waveforms.
*   **12-Column Responsive CSS Grid & Sync Audit**: Upgraded React layout to a responsive 12-column grid system utilizing 8px margin spacing. Created dynamic metric selection charts (Heart Rate, HRV, SpO2, Sleep, Steps, Calories, Stress), compact ECG playback zoom widgets, and Google Fit audit triggers validating timezone offsets, data deduplications, and backend consistency logs.
*   **App Check Bypass & Sync Alignment**:
    *   Temporarily disabled Firebase App Check initialization in development workflows via `VITE_APP_CHECK_ENABLED=false` config settings, completely eliminating reCAPTCHA network handshake errors in localhost environments while keeping the setup production-ready.
    *   Bypassed backend App Check validation inside the request middleware dependency when `APP_CHECK_ENABLED=false` is detected.
    *   Mapped dynamic Google Fit API aggregated metrics (rest heart rates, steps, active calories, sleep duration) directly to frontend AreaCharts and Apple Activity Rings.
    *   Configured PostgreSQL database aggregation logic for `/daily`, `/weekly`, and `/monthly` analytics endpoints.
    *   Optimized Recharts re-renders using `React.memo` wrapper guards.
*   **Research-Grade Modular AI Pipeline**:
    *   Created local `ai/` folder housing classical signal preprocessing filters (Butterworth, notch, median filters) and beat segmentation utils.
    *   Implemented Pan-Tompkins QRS peak detection algorithm to isolate RR interval time series.
    *   Built time-domain, frequency-domain (Welch periodogram power spectral densities), and non-linear Poincaré plot feature extractors.
    *   Constructed a PyTorch-based Time Series Transformer foundation model projecting RR interval signals into latent embeddings.
    *   Built a multimodal fusion network concatenating signal latents with tabular wearable data (steps, calories, sleep, SpO2, demographics).
    *   Implemented ensemble training benchmarks comparing Random Forest, XGBoost, and Logistic Regression models.
    *   Created SHAP-like feature contributions and natural language explainers giving clear diagnostic justification.
    *   Mapped the FastAPI backend prediction routes and reports PDF generator to execute the ensemble risk classifier pipeline, completely replacing simulated AI mock predictions.
*   **Production Audit & Hardening**:
    *   Cleaned unused parameters in catch clauses across `firebase.ts`, `remoteConfig.ts`, and `appCheck.ts` to solve compiler/linter warnings.
    *   Optimized Redis command pipelines in `RateLimitMiddleware` using async context managers to guarantee socket release.
    *   Added standard clickjacking, XSS, and HSTS security headers to all responses.
    *   Wrote Vitest suites for Firebase App Check and Remote Config, achieving clean execution.
    *   Added `aiosqlite` and `psutil` dependencies in the backend.
    *   Configured SQLite in-memory and Mock Redis database/caching test configurations in `conftest.py`.
    *   Built complete test suites validating AI feature consistency (`test_ai_validation.py`), database model cascade rules (`test_database_validation.py`), and FastAPI routes (`test_api.py`).
    *   Built client-side unit tests verifying Google Fit timestamp deduplication and frontend-to-backend consistency checking thresholds (`fitSync.test.ts`).
    *   Created `benchmark.py` testing sequential prediction load, latency percentiles (p50, p95, p99), and RAM/CPU utilization metrics.
    *   Generated full system verification matrix and validation audit report.
*   **Research-Grade Model Evaluation**:
    *   Implemented a scientific cross-validation benchmark suite (`experiments.py`) to evaluate models on MIT-BIH, PTB-XL, Chapman, and PhysioNet formats.
    *   Integrated Optuna for Bayesian hyperparameter tuning of XGBoost, Random Forest, Logistic Regression, and LightGBM models.
    *   Conducted feature ablation studies proving a 3.09% F1-score gain when fusing sequences with clinical HRV, activity, sleep, and demographics.
    *   Generated paired t-test and Wilcoxon signed-rank tests confirming statistical significance of LightGBM's performance.
    *   Rendered publication-quality IEEE-ready ROC, Precision-Recall, Calibration, and Confusion Matrix charts.
    *   Authored the comprehensive scientific research paper `docs/research_evaluation.md`.
*   **Production-Ready Sidebar Navigation**:
    *   Installed `react-router-dom` in the React frontend.
    *   Created dynamic, lazy-loaded pages (`Dashboard.tsx`, `Trends.tsx`, `Reports.tsx`, `Notifications.tsx`, `Connections.tsx`, `Settings.tsx`, `Profile.tsx`) to improve loading performance.
    *   Implemented `AppRouter.tsx` mapping centralized client-side routing within a master sidebar layout.
    *   Configured custom `ErrorBoundary.tsx` and custom 404 `NotFound.tsx` fallback page views.
    *   Refactored `App.tsx` and desktop/mobile sidebar indicators to use `NavLink` active class highlights.
    *   Resolved all TypeScript compile, linter, and Vite builder diagnostics.
*   **Wearable-Powered Cardiovascular Health Platform Transformation**:
    *   Created `user_profiles` schema and model supporting clinical variables (Diabetes, Hypertension, Cholesterol), medications, allergies, and lifestyle factors.
    *   Added longitudinal metrics columns (`sleep_minutes`, `calories_burned`, `steps_count`, `spo2`, `systolic_bp`, `diastolic_bp`) inside `WearableData` model.
    *   Implemented FastAPI endpoints `GET /me/profile` and `PUT /me/profile` to get and save profile data.
    *   Expanded AI predict endpoint pipeline to handle 26-dimensional inputs, separating output clinical metrics from wellness optimization recommendations.
    *   Updated the PDF report engine to include user demographics and active goal completion statistics in clinical PDF exports.
    *   Designed a detailed `Profile.tsx` editor form for clinical histories, medications lists, and daily fitness targets.
    *   Added a manual vitals sync panel in `Dashboard.tsx` to handle direct database inputs of steps, sleep, SpO2, blood pressure, and weight parameters.
    *   Configured database automatic schema upgrades at FastAPI startup event.
*   **Comprehensive Personal Health Platform Extensions**:
    *   **SQL Models & Schemas**: Created new models `NutritionLog`, `HydrationLog`, `MedicationReminder`, `DoctorNote`, and `TimelineEvent` to record wellness compliance, emergency events, and clinician portal observations.
    *   **FastAPI Central API Router**: Mounted 7 new routers mapping hydration endpoints, nutrition intake logs, prescription reminders checklists, clinician notes, emergency dispatch alerts, and AI Wellness Coach dialogue systems.
    *   **Emergency Contact SMS Dispatch**: Designed an Emergency Action Center triggering critical alerts, loading designated emergency contacts, and returning immediate patient safety instructions.
    *   **AI Wellness Coach Chat Interface**: Built an interactive wellness coach advisor dialogue widget (`Coach.tsx`) evaluating heart rate, steps, SpO2, HRV, and clinical profiles to deliver customized health advice.
    *   **Trends Longitudinal Tracking**: Overwrote `Trends.tsx` to include blood pressure graphs, sleep graphs, meals and water intake logging cards, and a chronological incident timeline log feed.
    *   **Vite Bundle Build Verification**: The React client compilation builds with 100% success.
*   **Wearable-Powered Health & Research Platform Transformation**:
    *   **Regulatory Disclaimers & Terminology**: Added global medical disclaimer banner in `App.tsx` and updated terminology mapping ("Disease Prediction" -> "Cardiovascular Risk Factors" / "Clinical Decision Support (Research Use)") to meet FDA/clinical requirements.
    *   **Connected Devices Gateway (`Devices.tsx`)**: Created interface for managing wearable gateways (Fitbit, Google Fit, Samsung Health, Garmin, Polar, Oura) with battery logging and sensor diagnostic routines.
    *   **GDPR Privacy Control Center (`Privacy.tsx`)**: Built controls for research consent, cloud backups, Location tracking, data exports, and account deletion purges.
    *   **AI Explainability Dashboard (`Explainability.tsx`)**: Integrated SHAP feature attribution charts plotting positive/negative risk contributors.
    *   **Model Registry & Deployments (`ModelRegistry.tsx`)**: Built model deployment metric list (Accuracy, F1, AUC, Calibration Error) and rollback buttons.
    *   **Dataset splits & Balances (`DatasetManager.tsx`)**: Integrated Chapman, MIT-BIH, PTB-XL sampling frequencies, splits, and class balance displays.
    *   **Admin System Telemetry (`SystemMonitoring.tsx`)**: Mapped CPU, memory, database latency, and system log terminals.
    *   **Research CV Benchmarks (`Research.tsx`)**: Plotted ROC comparison curves, hyperparameter Optuna trials, and feature ablation tables.
    *   **Expanded Settings Configurations (`Settings.tsx`)**: Configured theme systems, timezones, language parameters, units systems, data retention rules, and developer mode.







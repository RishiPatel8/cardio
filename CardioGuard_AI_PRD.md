# Product & Research Requirements Document (PRD)
## CardioGuard AI — Wearable-Based Early Detection of Cardiovascular Disorders Using AI

**Document type:** Major Project PRD (Academic + Prototype)
**Status:** Draft v1.0

---

## 1. Executive Summary

CardioGuard AI is a wearable-based cardiovascular risk monitoring platform that fuses physiological time-series data (ECG, heart rate, PPG, activity, sleep) with a hybrid CNN+LSTM deep learning pipeline to detect abnormal cardiovascular patterns and estimate early-stage risk. The system is explainable (SHAP), deployable at the edge (TensorFlow Lite), and presented through an interactive, consumer-grade web dashboard rather than a clinical-looking interface.

The project's contribution is not inventing new algorithms, but engineering and evaluating a coherent pipeline — signal preprocessing → CNN feature extraction → LSTM temporal modeling → risk prediction → explainability → edge deployment → dashboard — and benchmarking it against classical ML baselines.

---

## 2. Problem Statement

Cardiovascular disease is frequently detected late, after symptoms are already severe, because routine monitoring relies on episodic clinical checkups rather than continuous physiological observation. Consumer wearables already capture continuous ECG/PPG/heart-rate/activity/sleep data, but most wearable apps only display raw metrics (e.g., "92 BPM") without interpreting them for early risk.

**Problem:** There is no accessible, explainable, low-latency system that converts continuous wearable physiological signals into an interpretable, early cardiovascular risk estimate.

---

## 3. Goals & Non-Goals

### 3.1 Goals
- Build a hybrid CNN+LSTM model that predicts cardiovascular risk from wearable time-series data.
- Benchmark the hybrid model against SVM, Random Forest, and Decision Tree baselines.
- Provide feature-level explainability (SHAP) for every prediction.
- Demonstrate feasibility of on-device (edge) inference via TensorFlow Lite conversion.
- Present results through an interactive, longitudinal web dashboard.
- Produce a defensible research narrative: research questions, methodology, real experimental results.

### 3.2 Non-Goals
- This is **not** a certified medical diagnostic device. No claim of clinical diagnosis is made anywhere in the product.
- Not building a general fitness-tracking app (steps/calories are contextual signals only, not the product).
- Not building seven parallel production models — classical ML models are baselines only, not shipped predictors.
- Not targeting real-time hospital-grade ECG monitoring (12-lead clinical ECG is out of scope; wearable single/few-lead ECG is in scope).

---

## 4. Research Questions

| # | Question |
|---|---|
| RQ1 | Can wearable physiological data be used to identify cardiovascular abnormalities? |
| RQ2 | Does a CNN+LSTM approach effectively learn both signal-level features and temporal patterns? |
| RQ3 | How does the hybrid model compare against traditional ML approaches (SVM, Random Forest, Decision Tree)? |
| RQ4 | Can Edge AI (TensorFlow Lite) reduce dependency on cloud-based inference without materially hurting accuracy? |
| RQ5 | Can SHAP make cardiovascular AI predictions understandable to a non-clinical end user? |

Each RQ must be answered in the results section with real numbers, not assumed conclusions.

---

## 5. Users & Personas

| Persona | Need |
|---|---|
| **End user / wearer** | Wants a simple risk score with a plain-language "why", not raw signal dumps. |
| **Evaluator / clinician-in-the-loop (project reviewer role)** | Wants to see model performance, explainability, and a clear "not a diagnosis" boundary. |
| **You (developer/researcher)** | Needs a system that is demoable end-to-end and defensible in a viva — data → model → explanation → UI. |

---

## 6. System Architecture

### 6.1 High-Level Pipeline

```
WEARABLE DEVICE
      │
      ▼
Physiological Data: ECG · Heart Rate · PPG · Activity · Sleep
      │
      ▼
DATA PREPROCESSING  (denoising, motion-artifact handling, resampling, normalization)
      │
      ▼
FEATURE EXTRACTION
      │
      ▼
CNN  (spatial/morphological pattern extraction)
      │
      ▼
LSTM  (temporal / sequential pattern modeling)
      │
      ▼
CARDIOVASCULAR RISK PREDICTION
      │
   ┌──┴──┐
   ▼     ▼
 SHAP   Edge AI (TensorFlow Lite)
   │     │
   └──┬──┘
      ▼
 WEB DASHBOARD → Risk Score · Insights · Alerts · History
```

### 6.2 Component Breakdown

**A. Ingestion layer** — accepts wearable data (live stream or uploaded/simulated dataset for demo purposes). For the academic prototype, a public wearable ECG/PPG dataset stands in for live device data unless real hardware is available.

**B. Preprocessing layer**
- Missing-value handling
- Noise filtering (bandpass/notch filters for ECG)
- Motion-artifact suppression
- Resampling to a common rate across signal types
- Normalization / scaling
- SMOTE applied at training time only, on the feature/label set, to correct class imbalance (majority "normal" vs minority "abnormal" samples) — never applied to raw signals used for inference.

**C. Modeling layer**
- CNN: learns local morphological/waveform features from ECG/PPG windows.
- LSTM: learns how CNN-extracted features evolve across time.
- CNN+LSTM (primary/production model): feeds CNN feature maps into an LSTM for a final risk classification/regression head.
- Baselines (comparison only, not shipped): SVM, Random Forest, Decision Tree, trained on hand-engineered features from the same preprocessed data.

**D. Explainability layer** — SHAP values computed per prediction, aggregated into a ranked feature-contribution view (e.g., heart-rate pattern, ECG abnormality, low activity, poor sleep).

**E. Edge deployment layer** — trained CNN+LSTM converted to TensorFlow Lite; quantization evaluated for latency/accuracy trade-off; inference runnable without a network round-trip where the client supports it.

**F. Application layer (dashboard)** — consumes prediction + SHAP output + historical data and renders the UI (see Section 9).

### 6.4 Live Fitness-App Integration (New — Core Product Idea)

The core product idea is that the website itself is the ingestion point: a user connects their fitness app, the platform stores their physiological data over time, and predictions run against that stored history rather than a one-off upload.

**Recommended platform: Fitbit Web API**, for three practical reasons:
1. It's OAuth2-based and works from a pure web app — no native mobile companion app required (unlike Apple HealthKit, which only exposes data on-device via iOS).
2. It has a free developer sandbox with clear docs — the most achievable path for a student project timeline.
3. Unlike the Google Fit REST API (deprecated for new signups since May 2024, fully shut down by end of 2026 per Google's own migration guidance), Fitbit's Web API remains supported, and Google is folding equivalent server-side access into a new **Google Health API** for exactly this "cloud/account integration" use case — so Fitbit is the safer near-term choice, with Google Health API worth revisiting as a second data source later if time allows.

**Important scope-defining constraint:** none of these consumer platforms expose raw ECG waveform samples through their public APIs — Fitbit's ECG app results aren't queryable that way, and Apple Watch ECG traces stay inside Apple Health/HealthKit. So:
- **Model training** still uses a public ECG/PPG waveform dataset (as in Section 7) — this is where the CNN learns waveform morphology.
- **Live integration** supplies continuous heart rate, HRV (where available), resting heart rate, sleep, and activity — real time-series data that feeds the LSTM's temporal-trend modeling and a lighter "trend-based" risk pathway even when no ECG window is available for a given moment.
- Frame this honestly in your report: the system supports two prediction pathways — a full waveform-based pathway (ECG+HR+PPG, used when ECG data is present, e.g. from a research dataset or an ECG-capable device export) and a trend-based pathway (HR/HRV/sleep/activity only, used for continuous live monitoring via the fitness-app connection). This is a legitimate design decision, not a limitation to hide.

**Connect flow:**
```
User clicks "Connect Fitbit"
        ↓
OAuth2 authorization (Fitbit consent screen)
        ↓
Website receives access token + refresh token
        ↓
Tokens stored (encrypted) against the user's account in Firebase
        ↓
Backend sync job begins pulling that user's data on a schedule
```

**Sync & inference flow:**
```
Scheduled job (e.g. Firebase Cloud Function, cron-triggered)
        ↓
For each connected user: refresh token if expired
        ↓
Pull intraday heart rate, HRV, sleep, activity from Fitbit Web API
        ↓
Normalize into internal schema (Section 6.5)
        ↓
Preprocessing (Section 6.2) → feature windows
        ↓
CNN+LSTM inference (trend-based pathway) OR full pathway if ECG present
        ↓
SHAP explanation generated
        ↓
Prediction + explanation written to Firestore
        ↓
Dashboard reads latest prediction; alert fires if risk crosses threshold
```

**Phase-in plan (per your answer — simulate now, real device later):**
- **Now:** build a simulator module that generates data shaped *exactly* like the Fitbit API response schema (same fields, same units, same cadence). All downstream code — normalization, storage, preprocessing, inference — is built against that schema from day one.
- **Later:** swap the simulator for the real OAuth+API calls. Because the schema was matched from the start, nothing downstream of ingestion needs to change — this is the whole point of designing it this way now rather than retrofitting it after the demo works on fake data.

### 6.5 Data Storage Schema (Firebase Firestore)

| Collection | Purpose | Key fields |
|---|---|---|
| `users` | Account + profile | uid, name, created_at |
| `connections` | Fitness-app link per user | provider (fitbit), access_token (encrypted), refresh_token (encrypted), expires_at, connected_at |
| `raw_readings` | Normalized ingested data | user_id, source (fitbit / simulator / dataset), signal_type (hr/hrv/sleep/activity/ecg), timestamp, value(s) |
| `feature_windows` | Preprocessed model-ready windows | user_id, window_start, window_end, features (vector), pathway (trend/full) |
| `predictions` | Model outputs | user_id, timestamp, risk_score, risk_tier, model_version, pathway |
| `explanations` | SHAP output per prediction | prediction_id, feature_contributions (ranked list) |
| `alerts` | Threshold-triggered notifications | user_id, prediction_id, message, acknowledged (bool), created_at |

**Storage rules:**
- Raw tokens are never exposed to the frontend — only the backend/Cloud Functions touch `connections`.
- Every row in `predictions` must have a matching row in `explanations` before it's surfaced to the dashboard (enforces Section 10, Rule 2 — explainability is mandatory).
- `raw_readings.source` is always recorded, so the report can honestly state which predictions ran on simulated vs. real vs. dataset-sourced data.

### 6.6 Data Flow Rules
1. Raw signals never reach the model directly — they always pass through the preprocessing layer first.
2. SMOTE is a **training-time-only** step; it must never be applied to live inference data.
3. Every prediction returned to the UI must be accompanied by a SHAP explanation payload — the UI must never display a bare risk score with no "why."
4. Every risk output is labeled as an AI-generated indication, explicitly not a medical diagnosis, both in the API response and in the UI.
5. `raw_readings.source` (simulator / real device / research dataset) is always recorded and never silently mixed without labeling — the dashboard and report must be able to distinguish them.

---

## 7. Data

### 7.1 Signal Types

| Signal | Role |
|---|---|
| ECG | Electrical activity of the heart; primary source of abnormal-beat/morphology detection |
| Heart rate | Trend and variability over time |
| PPG | Optical pulse signal, secondary cardiovascular indicator |
| Activity | Contextual signal (movement/steps) |
| Sleep | Contextual signal (duration/pattern) |

### 7.2 Data Requirements
- Time-series, windowed (e.g., fixed-length sliding windows per signal) for CNN input.
- Labeled as normal/abnormal (or risk tiers) for supervised training.
- Class distribution should be documented explicitly (expect imbalance; this is why SMOTE is used).
- If using public datasets for the academic prototype (e.g., PhysioNet-style ECG datasets), the dataset name, size, class balance, and preprocessing steps must be documented in the methodology section for reproducibility.

---

## 8. Models

### 8.1 CNN — Feature Extraction
Learns local waveform/morphological patterns (abnormal beats, structural signal features) from windowed signal input.

### 8.2 LSTM — Temporal Modeling
Learns how extracted features change across time steps (e.g., a rising heart-rate trend across successive windows).

### 8.3 CNN+LSTM — Primary Model
CNN output feeds into LSTM; LSTM output feeds into a classification/regression head producing the risk score. This is the model that ships to the dashboard and to Edge AI conversion.

### 8.4 Baselines (comparison only)
SVM, Random Forest, Decision Tree — trained on hand-engineered summary features (e.g., HRV statistics, beat morphology descriptors) extracted from the same preprocessed data. Used purely to contextualize CNN+LSTM performance; not deployed.

### 8.5 Class Imbalance Handling
SMOTE generates synthetic minority-class (abnormal) samples at training time to prevent majority-class bias.

### 8.6 Evaluation Metrics
Accuracy, Precision, Recall, F1-score, AUC — computed for every model (baselines + CNN + LSTM + CNN+LSTM) on the same held-out test split, reported in a single comparison table with **actual** experimental numbers.

| Model | Accuracy | Precision | Recall | F1 | AUC |
|---|---|---|---|---|---|
| SVM | — | — | — | — | — |
| Random Forest | — | — | — | — | — |
| Decision Tree | — | — | — | — | — |
| CNN | — | — | — | — | — |
| LSTM | — | — | — | — | — |
| **CNN + LSTM** | — | — | — | — | — |

### 8.7 Explainability — SHAP
Per-prediction SHAP values ranked by contribution magnitude, surfaced to the UI as a ranked bar-style breakdown (e.g., heart-rate pattern, ECG abnormality, low activity, poor sleep).

### 8.8 Edge AI — TensorFlow Lite
- Train in TensorFlow/Keras.
- Convert the final CNN+LSTM model to TensorFlow Lite.
- Evaluate quantized vs full-precision accuracy and latency.
- Document the accuracy/latency trade-off as part of RQ4.

---

## 9. Web Dashboard / UX

### 9.1 Design Direction
Consumer-grade, continuous-monitoring feel — closer to Apple Fitness / WHOOP / Garmin Connect than a hospital chart. Interactive, not static.

### 9.2 Public Website Sections
Hero → Problem → Why early detection matters → Wearable technology → How the AI works → Interactive architecture (scroll-linked animation of the pipeline) → CNN+LSTM explanation → Edge AI → Explainable AI → Research/literature → Benefits → Call to action.

### 9.3 Product Dashboard Sections
Overview → Live monitoring → ECG (interactive: zoom/pan/inspect/abnormal-region highlighting) → Heart rate → AI prediction → SHAP insights → Alerts → History (today/yesterday/last week/last month trends) → Reports → Settings.

### 9.4 Core Dashboard Modules
- **Heart:** current HR, HR trend, ECG waveform, signal quality indicator.
- **Recovery:** sleep, activity, recovery indicators.
- **AI:** risk score, prediction, confidence, SHAP explanation.
- **Alerts:** abnormal-pattern and elevated-risk notifications, each paired with a "why" explanation and the mandatory non-diagnostic disclaimer.

### 9.5 Interaction Design
Scroll-triggered and scroll-linked animation used specifically to make the *pipeline itself* legible on the public site (wearable → data flowing → CNN activates → LSTM activates → risk meter fills → SHAP explanation appears → final prediction). This is a communication tool, not just decoration — it should visually mirror Section 6.1.

---

## 10. Non-Functional Requirements & Rules

1. **No diagnostic claims.** Every risk output, alert, and report must state clearly that it is an AI-generated indication, not a medical diagnosis, and should recommend professional consultation for high-risk results.
2. **Explainability is mandatory, not optional.** No prediction may be shown without its SHAP-based explanation.
3. **Data provenance and privacy.** Physiological data is sensitive; document how data is stored/handled, and prefer on-device inference (Edge AI) where possible to minimize cloud transmission of raw signals.
4. **Reproducibility.** Preprocessing steps, dataset details, train/test split, and hyperparameters must be documented well enough that results are reproducible.
5. **No fabricated results.** All accuracy/precision/recall/F1/AUC figures reported must come from actual experiments — never presented as placeholder or assumed numbers in the final report.
6. **Scope discipline.** Classical ML models (SVM/RF/DT) are baselines only — they are not to be built out as parallel production features; this keeps the implementation scope achievable for a single project team.
7. **Model boundary discipline.** SMOTE is a training-time-only balancing step and must never touch live inference data.

---

## 11. Technology Stack (indicative)

| Layer | Technology |
|---|---|
| Model training | Python, TensorFlow/Keras (CNN, LSTM, CNN+LSTM) |
| Baselines | scikit-learn (SVM, Random Forest, Decision Tree) |
| Imbalance handling | imbalanced-learn (SMOTE) |
| Explainability | SHAP |
| Edge deployment | TensorFlow Lite |
| Frontend/dashboard | Next.js |
| Backend/data | Firebase |
| Client-side inference (optional) | TensorFlow.js |

---

## 12. Project Phases

### Phase 0 — Ingestion Scaffold (Week 1, runs alongside Phase 1)
- Define the internal data schema (Section 6.5) once, up front.
- Build the Fitbit-shaped simulator that generates HR/HRV/sleep/activity data matching that schema.
- Stand up the storage layer (`users`, `connections`, `raw_readings`) so every later phase writes to the real schema from day one instead of throwaway test code.
- This is what makes "simulate now, connect a real device later" actually painless — the swap only touches ingestion, nothing downstream.

### Phase 1 — Foundations (Weeks 1–2)
- Finalize dataset(s), document class balance and signal types.
- Build preprocessing pipeline (denoising, resampling, normalization).
- Literature survey consolidation (mapping papers already reviewed to RQ1–RQ5).

### Phase 2 — Baseline Modeling (Weeks 3–4)
- Feature engineering for classical ML.
- Train/evaluate SVM, Random Forest, Decision Tree.
- Establish the baseline rows of the results table.

### Phase 3 — Deep Learning Core (Weeks 5–7)
- Build and train CNN (standalone), LSTM (standalone), and CNN+LSTM (hybrid).
- Apply SMOTE at training time; validate impact on minority-class recall.
- Complete the full results comparison table with real metrics.

### Phase 4 — Explainability & Edge AI (Weeks 8–9)
- Integrate SHAP for the CNN+LSTM model; validate explanations are stable and sensible.
- Convert CNN+LSTM to TensorFlow Lite; benchmark accuracy/latency vs full model (RQ4).

### Phase 5 — Dashboard & Integration (Weeks 10–12)
- Build the public site and product dashboard per Section 9.
- Wire model + SHAP output into the dashboard (risk score, insights, alerts, history).
- Implement mandatory disclaimers throughout.
- Build the real Fitbit OAuth "Connect" flow and swap it in behind the same ingestion schema the simulator used (Section 6.4) — this becomes the "real device later" milestone.

### Phase 6 — Evaluation, Report, Demo (Weeks 13–14)
- Finalize results table and answer RQ1–RQ5 explicitly with evidence.
- Prepare research paper / report, PPT, and end-to-end live demo script (Section 13 of source notes: wearable data → preprocessing → CNN → LSTM → CNN+LSTM → prediction → SHAP/Edge AI → dashboard → risk/insights/alerts).

---

## 13. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Dataset too small/imbalanced for deep learning to outperform baselines | Use SMOTE, report honestly if a baseline wins on some metric — this is a valid, defensible research finding |
| CNN+LSTM overfits on limited wearable data | Cross-validation, regularization, keep architecture depth proportionate to dataset size |
| TFLite conversion degrades accuracy significantly | Report the trade-off transparently as part of RQ4 rather than hiding it |
| Scope creep on the dashboard (too many features, too little model rigor) | Treat Section 6 (pipeline) and Section 8 (models/metrics) as the core deliverable; dashboard is the presentation layer, not the contribution |
| Reviewers questioning medical-claim overreach | Enforce Section 10 Rule 1 (non-diagnostic disclaimer) everywhere, consistently |

---

## 14. Final Deliverables Checklist

- [ ] Preprocessing pipeline (documented, reproducible)
- [ ] Trained SVM, Random Forest, Decision Tree baselines
- [ ] Trained CNN, LSTM, CNN+LSTM models
- [ ] Full results comparison table with real metrics
- [ ] SHAP explanation integration
- [ ] TensorFlow Lite conversion + latency/accuracy benchmark
- [ ] Public website (architecture storytelling, scroll-linked)
- [ ] Product dashboard (risk score, insights, alerts, history)
- [ ] Non-diagnostic disclaimer present on every risk-related surface
- [ ] Research report answering RQ1–RQ5 with evidence
- [ ] PPT + live demo script aligned to Section 6.1 pipeline

---

## 15. One-Sentence Project Definition

CardioGuard AI is an AI-powered wearable health platform that uses a CNN+LSTM hybrid model to analyze physiological time-series data, TensorFlow Lite for on-device edge inference, and SHAP for explainable cardiovascular-risk prediction, presented through an interactive, Apple Fitness/WHOOP-style web dashboard — explicitly framed as an early-risk indicator, not a medical diagnosis.

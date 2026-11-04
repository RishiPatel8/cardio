# CardioGuard AI - Current Status

## 1. Backend Dependencies & Environment
- **Status**: 🟡 PARTIAL (Fixed)
- **Evidence**: `fastapi` and `uvicorn` were missing in `.venv` but were successfully installed via `pip install fastapi uvicorn`.
- **Blockers**: None. Backend can now be started.

## 2. Deep Learning Execution & TensorFlow
- **Status**: 🔴 BLOCKED
- **Evidence**: `import tensorflow as tf` globally fails with `ImportError: DLL load failed while importing pywrap_function_lib: An Application Control policy has blocked this file.` WDAC OS-level security prevents TF DLL execution.
- **Blockers**: OS Security Policy. 100% dataset training and TFLite regeneration are physically blocked on this machine.

## 3. Backend Real Inference
- **Status**: 🟡 PARTIAL
- **Evidence**: `predict.py` was previously modified to use `PreprocessingPipeline` and `shap_background.npy`.
- **Blockers**: 
  - `predict.py` currently silently falls back to DEMO mode if `tf` is not installed or fails to load. This violates the strict "REAL mode must fail clearly" rule.
  - Since WDAC blocks TF, REAL inference will always fail. We must handle this gracefully.

## 4. SHAP Background
- **Status**: ✅ DONE
- **Evidence**: `shap_background.npy` was generated successfully without TF using `generate_shap_bg.py`.

## 5. TFLite Regeneration
- **Status**: 🔴 BLOCKED
- **Evidence**: TFLite conversion requires TensorFlow, which is blocked by WDAC. We will rely on historical artifacts.

## 6. Firestore Security
- **Status**: 🔴 BLOCKED (Security Issue)
- **Evidence**: Raw service account JSON (`cardiogaurd-ai-firebase-adminsdk-fbsvc-fb5d5ae8ea.json`) is committed to the repository in `backend/`. This is a security violation.

## 7. Frontend E2E
- **Status**: ⚪ NOT VERIFIED
- **Evidence**: Frontend builds successfully (`npm run build`). Will be verified against the backend.

## 8. Android
- **Status**: ⚪ NOT VERIFIED
- **Evidence**: Scaffolding exists but no build environment verified.

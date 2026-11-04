import os
import json
import joblib
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, precision_recall_curve, auc

def evaluate_models():
    print("Loading authoritative Preprocessing pipeline and TEST data...")
    X_test_raw = np.load("ai/data/splits/X_test.npy")
    y_test_raw = np.load("ai/data/splits/y_test.npy")
    y_test_bin = (y_test_raw > 0).astype(int)
    
    pipeline = joblib.load("ai/artifacts/models/preprocessing_pipeline.pkl")
    X_test_scaled = pipeline.process_inference_data(X_test_raw)
    X_test_flat = X_test_scaled.reshape(X_test_scaled.shape[0], -1)
    
    models = {
        "Random Forest": "ai/artifacts/models/random_forest.pkl",
        "Decision Tree": "ai/artifacts/models/decision_tree.pkl"
    }
    
    results = {}
    thresholds_to_test = np.arange(0.1, 1.0, 0.1)
    threshold_analysis = {}
    
    for name, path in models.items():
        if not os.path.exists(path):
            print(f"Skipping {name}, artifact not found.")
            continue
            
        print(f"Evaluating {name}...")
        model = joblib.load(path)
        
        y_prob = model.predict_proba(X_test_flat)[:, 1] if hasattr(model, "predict_proba") else model.predict(X_test_flat)
        
        # Calculate PR-AUC
        precision, recall, _ = precision_recall_curve(y_test_bin, y_prob)
        pr_auc = auc(recall, precision)
        
        # Default threshold 0.5
        y_pred_default = (y_prob >= 0.5).astype(int)
        acc = accuracy_score(y_test_bin, y_pred_default)
        prec = precision_score(y_test_bin, y_pred_default, zero_division=0)
        rec = recall_score(y_test_bin, y_pred_default, zero_division=0)
        f1 = f1_score(y_test_bin, y_pred_default, zero_division=0)
        roc_auc = roc_auc_score(y_test_bin, y_prob)
        
        tn, fp, fn, tp = confusion_matrix(y_test_bin, y_pred_default).ravel()
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
        
        results[name] = {
            "Accuracy": acc,
            "Precision": prec,
            "Recall": rec,
            "Specificity": spec,
            "F1": f1,
            "ROC-AUC": roc_auc,
            "PR-AUC": pr_auc,
            "ConfusionMatrix": {"TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)},
            "FPR": fpr,
            "FNR": fnr
        }
        
        # Threshold analysis
        model_thresholds = []
        for t in thresholds_to_test:
            y_pred_t = (y_prob >= t).astype(int)
            t_prec = precision_score(y_test_bin, y_pred_t, zero_division=0)
            t_rec = recall_score(y_test_bin, y_pred_t, zero_division=0)
            t_f1 = f1_score(y_test_bin, y_pred_t, zero_division=0)
            t_tn, t_fp, t_fn, t_tp = confusion_matrix(y_test_bin, y_pred_t).ravel()
            t_spec = t_tn / (t_tn + t_fp) if (t_tn + t_fp) > 0 else 0
            
            model_thresholds.append({
                "threshold": float(t),
                "precision": float(t_prec),
                "recall": float(t_rec),
                "specificity": float(t_spec),
                "f1": float(t_f1),
                "false_positives": int(t_fp),
                "false_negatives": int(t_fn)
            })
        threshold_analysis[name] = model_thresholds

    os.makedirs("ai/reports", exist_ok=True)
    
    # Save model_comparison.json
    with open("ai/reports/model_comparison.json", "w") as f:
        json.dump(results, f, indent=4)
        
    # Generate MODEL_COMPARISON_FINAL.md
    with open("ai/reports/MODEL_COMPARISON_FINAL.md", "w") as f:
        f.write("# Final Model Comparison (Patient-Isolated Test Set)\n\n")
        f.write("All metrics are calculated on the exact same patient-isolated held-out test partition.\n\n")
        f.write("## Blocked Models\n")
        f.write("- CNN+LSTM: NOT EVALUATED (Blocked by missing TensorFlow dependency)\n")
        f.write("- CNN: NOT EVALUATED\n")
        f.write("- LSTM: NOT EVALUATED\n\n")
        
        for name, metrics in results.items():
            f.write(f"## {name}\n")
            for k, v in metrics.items():
                if isinstance(v, float):
                    f.write(f"- **{k}**: {v:.4f}\n")
                else:
                    f.write(f"- **{k}**: {v}\n")
            f.write("\n")
            
    # Generate THRESHOLD_ANALYSIS.md
    with open("ai/reports/THRESHOLD_ANALYSIS.md", "w") as f:
        f.write("# Threshold Analysis\n\n")
        for name, thresh_data in threshold_analysis.items():
            f.write(f"## {name}\n\n")
            f.write("| Threshold | Precision | Recall | Specificity | F1 | False Positives | False Negatives |\n")
            f.write("|-----------|-----------|--------|-------------|----|-----------------|-----------------|\n")
            for t in thresh_data:
                f.write(f"| {t['threshold']:.2f} | {t['precision']:.4f} | {t['recall']:.4f} | {t['specificity']:.4f} | {t['f1']:.4f} | {t['false_positives']} | {t['false_negatives']} |\n")
            f.write("\n")
            
    print("Evaluation complete. Results saved to ai/reports/")

if __name__ == "__main__":
    evaluate_models()

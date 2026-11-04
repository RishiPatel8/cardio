import os
import json
import joblib
import pandas as pd
import numpy as np

from ai.explainability.shap_explainer import SHAPExplainer

def run_shap():
    print("=" * 50)
    print("PHASE 6 & 7: SHAP EXPLAINER")
    print("=" * 50)
    
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    train_path = os.path.join(PROJECT_ROOT, "ai/datasets/mitbih_train.csv")
    test_path = os.path.join(PROJECT_ROOT, "ai/datasets/mitbih_test.csv")
    scaler_path = os.path.join(PROJECT_ROOT, "ai/artifacts/models/scaler.pkl")
    model_path = os.path.join(PROJECT_ROOT, "ai/artifacts/models/cnn_lstm/cnn_lstm.h5")
    
    train_df = pd.read_csv(train_path, header=None)
    test_df = pd.read_csv(test_path, header=None)
    
    scaler = joblib.load(scaler_path)
    
    # Take background data from training set (100 samples)
    background_raw = train_df.iloc[:100, :186].values
    background_scaled = scaler.transform(pd.DataFrame(background_raw).ffill().bfill().values)
    background_dl = background_scaled.reshape(100, 186, 1)
    
    print("Initializing KernelExplainer...")
    explainer = SHAPExplainer(model_path, background_dl)
    
    # Take 5 samples to explain from test set
    explain_raw = test_df.iloc[:5, :186].values
    explain_scaled = scaler.transform(pd.DataFrame(explain_raw).ffill().bfill().values)
    explain_dl = explain_scaled.reshape(5, 186, 1)
    
    shap_dir = os.path.join(PROJECT_ROOT, "ai/results/shap")
    os.makedirs(shap_dir, exist_ok=True)
    
    all_shap_values = []
    summary_data = []
    
    for i in range(5):
        print(f"Explaining sample {i}...")
        contributions = explainer.explain(explain_dl[i:i+1])
        all_shap_values.append(contributions)
        for c in contributions:
            summary_data.append({"sample": i, "feature": c["feature"], "contribution": c["contribution"]})
            
    with open(os.path.join(shap_dir, "shap_values.json"), "w") as f:
        json.dump(all_shap_values, f, indent=4)
        
    pd.DataFrame(summary_data).to_csv(os.path.join(shap_dir, "shap_summary.csv"), index=False)
    print("SHAP values and summary saved to ai/results/shap/")

if __name__ == "__main__":
    run_shap()

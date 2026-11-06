import os
import sys
import numpy as np

sys.path.insert(0, r"g:/cardio")

from backend.app.services.shap_service import get_shap_service

def test():
    # Set prediction mode to real
    os.environ["PREDICTION_MODE"] = "real"
    
    model_path = r"g:/cardio\ai\artifacts\models\v6_full\best_model.h5"
    bg_path = r"g:/cardio\ai\artifacts\models\v6_full\shap_background.npy"
    
    print("Loading ShapService...")
    shap_service = get_shap_service(model_path, bg_path)
    
    sample = np.random.randn(1000)
    
    print("Getting explanation...")
    # Target class 1 for testing
    contributions = shap_service.get_explanation(sample, target_class=1)
    
    print(f"Returned {len(contributions)} contributions.")
    if len(contributions) > 0:
        print("Top 5 contributions:")
        for c in contributions[:5]:
            print(f" - {c['feature']}: {c['contribution']}")
    else:
        print("FAIL: No contributions returned.")

if __name__ == "__main__":
    test()


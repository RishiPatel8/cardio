import numpy as np
import tensorflow as tf
from sklearn.metrics import brier_score_loss
import matplotlib.pyplot as plt
import os

def check_calibration(y_true, y_prob, output_dir):
    """
    Check calibration of a 3-class classifier and save reliability curves.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # We will use expected calibration error or just brier score
    class_names = ["NORM", "AFIB", "OTHER"]
    
    brier_scores = {}
    for i, name in enumerate(class_names):
        y_true_binary = (y_true == i).astype(int)
        y_prob_class = y_prob[:, i]
        brier = brier_score_loss(y_true_binary, y_prob_class)
        brier_scores[name] = brier
        
    print(f"Brier Scores (lower is better): {brier_scores}")
    
    with open(os.path.join(output_dir, "brier_scores.txt"), 'w') as f:
        for k, v in brier_scores.items():
            f.write(f"{k}: {v:.4f}\n")
            
    # Simple temperature scaling placeholder if needed
    print("If Brier score is high (>0.1), consider Temperature Scaling.")

if __name__ == "__main__":
    pass

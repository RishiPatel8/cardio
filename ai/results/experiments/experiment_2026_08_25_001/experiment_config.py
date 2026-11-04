import os
from datetime import datetime

class ExperimentConfig:
    # General
    RANDOM_SEED = 42
    # Paths (Portable)
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    DATASET_PATH_TRAIN = os.path.join(PROJECT_ROOT, "ai/datasets/mitbih_train.csv")
    DATASET_PATH_TEST = os.path.join(PROJECT_ROOT, "ai/datasets/mitbih_test.csv")
    EXPERIMENT_ID = f"experiment_{datetime.utcnow().strftime('%Y_%m_%d_%H%M%S')}"
    
    # Preprocessing
    SAMPLING_RATE = 125
    WINDOW_SIZE = 187
    
    # Classification Task
    # Mapping MIT-BIH (0=N, 1=S, 2=V, 3=F, 4=Q) to Binary (0=Normal, 1=Abnormal)
    CLASSIFICATION_TASK = "binary_arrhythmia"
    
    # Training
    BATCH_SIZE = 64
    EPOCHS = 3  # Reduced for timely automated execution
    LEARNING_RATE = 0.001
    DROPOUT = 0.5
    
    # Output paths
    BASE_RESULTS_DIR = os.path.join(PROJECT_ROOT, f"ai/results/experiments/{EXPERIMENT_ID}")
    BASE_ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "ai/artifacts/models")
    
    # Whether to subsample dataset for faster execution during dev loop
    SUBSAMPLE_RATIO = 0.05 # 5% of data for rapid execution in this automated test loop

config = ExperimentConfig()

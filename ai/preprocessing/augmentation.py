import numpy as np

def augment_ecg_batch(X, noise_std=0.01, baseline_shift=0.1):
    """
    Applies medically reasonable data augmentation to a batch of ECGs.
    
    Args:
        X: Numpy array of shape (batch_size, time_steps, 1)
        noise_std: Standard deviation of Gaussian noise
        baseline_shift: Magnitude of random constant baseline shift
        
    Returns:
        X_aug: Augmented Numpy array
    """
    batch_size, time_steps, channels = X.shape
    X_aug = X.copy()
    
    # 1. Add Gaussian Noise
    noise = np.random.normal(0, noise_std, size=(batch_size, time_steps, channels))
    X_aug += noise
    
    # 2. Add Baseline Shift
    shifts = np.random.uniform(-baseline_shift, baseline_shift, size=(batch_size, 1, channels))
    X_aug += shifts
    
    return X_aug

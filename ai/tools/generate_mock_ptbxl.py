import os
import numpy as np

def generate_mock():
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'processed_ptbxl'))
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate 100 samples of 1000 length
    X = np.random.randn(100, 1000)
    y = np.random.randint(0, 3, size=(100,))
    
    # 80 for train (folds 1-8), 10 for val (fold 9), 10 for test (fold 10)
    folds = np.concatenate([
        np.random.randint(1, 9, size=(80,)),
        np.full((10,), 9),
        np.full((10,), 10)
    ])
    
    np.save(os.path.join(output_dir, 'X.npy'), X)
    np.save(os.path.join(output_dir, 'y.npy'), y)
    np.save(os.path.join(output_dir, 'folds.npy'), folds)
    
    print(f"Generated mock PTB-XL data at {output_dir}")

if __name__ == "__main__":
    generate_mock()

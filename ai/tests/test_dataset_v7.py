import os
import numpy as np

def test_patient_leakage():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'datasets', 'processed', 'v7'))
    
    train_pts = set(np.load(os.path.join(base_dir, 'train', 'patients.npy')))
    val_pts = set(np.load(os.path.join(base_dir, 'val', 'patients.npy')))
    test_pts = set(np.load(os.path.join(base_dir, 'test', 'patients.npy')))
    
    assert train_pts.isdisjoint(val_pts), "Leakage: Train intersects Val"
    assert train_pts.isdisjoint(test_pts), "Leakage: Train intersects Test"
    assert val_pts.isdisjoint(test_pts), "Leakage: Val intersects Test"

def test_ecg_shape():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'datasets', 'processed', 'v7'))
    
    for split in ['train', 'val', 'test']:
        X = np.load(os.path.join(base_dir, split, 'X.npy'))
        assert len(X.shape) == 2, f"{split} X shape is not 2D"
        assert X.shape[1] == 1000, f"{split} X length is not 1000"

def test_labels():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'datasets', 'processed', 'v7'))
    
    for split in ['train', 'val', 'test']:
        y = np.load(os.path.join(base_dir, split, 'y.npy'))
        unique_classes = set(np.unique(y))
        assert unique_classes.issubset({0, 1, 2, 3}), f"Invalid labels found in {split}: {unique_classes}"

def test_nan_inf():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'datasets', 'processed', 'v7'))
    
    for split in ['train', 'val', 'test']:
        X = np.load(os.path.join(base_dir, split, 'X.npy'))
        assert not np.isnan(X).any(), f"NaNs found in {split} X"
        assert not np.isinf(X).any(), f"Infs found in {split} X"

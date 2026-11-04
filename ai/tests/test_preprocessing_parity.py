import pytest
import numpy as np
from ai.preprocessing.pipeline import PreprocessingPipeline

def test_preprocessing_scaler_isolation():
    pipeline = PreprocessingPipeline(window_size=187)
    
    # Mock data
    X_train = np.random.rand(100, 187)
    X_test = np.random.rand(20, 187)
    
    # Process train
    train_transformed = pipeline.process_training_data(X_train)
    assert pipeline.is_fitted == True
    
    # Process test
    # If the pipeline incorrectly fit on test data, the internal scaler mean/var would change
    mean_before = pipeline.scaler.mean_.copy()
    var_before = pipeline.scaler.var_.copy()
    
    test_transformed = pipeline.process_inference_data(X_test)
    
    # Prove they didn't change
    np.testing.assert_array_equal(mean_before, pipeline.scaler.mean_)
    np.testing.assert_array_equal(var_before, pipeline.scaler.var_)

def test_unfitted_transform_fails():
    pipeline = PreprocessingPipeline(window_size=187)
    X_test = np.random.rand(20, 187)
    
    with pytest.raises(ValueError):
        pipeline.process_inference_data(X_test)

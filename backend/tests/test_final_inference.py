import pytest
import os
from app.services.inference_service import InferenceService

def test_inference_rejects_invalid_waveform():
    os.environ["PREDICTION_MODE"] = "real"
    service = InferenceService()
    
    # Missing waveform
    with pytest.raises(Exception, match="Payload missing 'waveform'"):
        service.run_inference({"not_waveform": [1,2,3]})
        
    # Wrong length (186) will hit SQI first if flatline
    with pytest.raises(Exception, match="SQI Error: Signal variance too low"):
        service.run_inference({"waveform": [0.0] * 186})
        
    # Wrong length (188) but with variance
    import numpy as np
    import random
    with pytest.raises(Exception, match="Invalid waveform length"):
        service.run_inference({"waveform": [float(random.random()) for _ in range(188)]})
        
    # NaN values
    import numpy as np
    with pytest.raises(Exception, match="Waveform contains invalid values"):
        service.run_inference({"waveform": [np.nan] + [0.0] * 186})
        
    # Inf values
    with pytest.raises(Exception, match="Waveform contains invalid values"):
        service.run_inference({"waveform": [np.inf] + [0.0] * 186})

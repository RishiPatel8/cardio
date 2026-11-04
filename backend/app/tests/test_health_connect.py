import pytest
from app.services.health_connect_service import HealthConnectService

def test_health_connect_processes_payload(monkeypatch):
    class MockRepo:
        def __init__(self, name):
            self.name = name
        def create(self, user_id, data):
            return "mock_doc_id"
            
    service = HealthConnectService()
    monkeypatch.setattr(service, "health_repo", MockRepo("health_connect"))
    
    payload = {
        "heart_rate": 72,
        "resting_heart_rate": 60,
        "steps": 1000
    }
    
    result = service.process_sync_payload("user_123", payload)
    
    assert result["status"] == "success"
    assert result["doc_id"] == "mock_doc_id"
    assert "timestamp" in result

def test_health_connect_rejects_ecg_waveform(monkeypatch):
    class MockRepo:
        def __init__(self, name):
            self.name = name
        def create(self, user_id, data):
            return "mock_doc_id"
            
    service = HealthConnectService()
    monkeypatch.setattr(service, "health_repo", MockRepo("health_connect"))
    
    payload = {
        "heart_rate": 72,
        "waveform": [0.0] * 187  # Attempting to sneak ECG data in
    }
    
    with pytest.raises(ValueError, match="cannot process ECG waveforms"):
        service.process_sync_payload("user_123", payload)
        
    payload_ecg = {
        "heart_rate": 72,
        "ecg_waveform": [0.0] * 187
    }
    
    with pytest.raises(ValueError, match="cannot process ECG waveforms"):
        service.process_sync_payload("user_123", payload_ecg)

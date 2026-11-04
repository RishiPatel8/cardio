import pytest
from app.services.google_health_service import GoogleHealthService
import time

def test_oauth_state_generation():
    service = GoogleHealthService()
    uid = "test_user_123"
    
    # Generate state
    state = service._generate_state(uid)
    
    # Assert state format
    parts = state.split(".")
    assert len(parts) == 3
    assert parts[0] == uid
    assert int(parts[1]) <= int(time.time())
    
def test_oauth_state_validation():
    service = GoogleHealthService()
    uid = "test_user_456"
    
    state = service._generate_state(uid)
    
    # Valid state should return UID
    extracted_uid = service._verify_state(state)
    assert extracted_uid == uid
    
def test_oauth_state_invalid_signature():
    service = GoogleHealthService()
    uid = "test_user_789"
    
    state = service._generate_state(uid)
    # Tamper with signature
    parts = state.split(".")
    parts[2] = "tampered_signature"
    bad_state = ".".join(parts)
    
    with pytest.raises(ValueError, match="Malformed or invalid OAuth state."):
        service._verify_state(bad_state)

def test_oauth_state_expired():
    service = GoogleHealthService()
    uid = "test_user_expired"
    
    # Forge an expired state (older than 900 seconds)
    expired_time = int(time.time()) - 1000
    message = f"{uid}:{expired_time}"
    import hmac, hashlib
    signature = hmac.new(
        service.client_secret.encode(), 
        message.encode(), 
        hashlib.sha256
    ).hexdigest()
    
    bad_state = f"{uid}.{expired_time}.{signature}"
    
    with pytest.raises(ValueError, match="Malformed or invalid OAuth state."):
        service._verify_state(bad_state)

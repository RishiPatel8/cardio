import random
from typing import Dict, Any
from datetime import datetime

class BaseConnection:
    def fetch_recent_data(self, user_id: str) -> Dict[str, Any]:
        raise NotImplementedError

class SimulatorConnection(BaseConnection):
    def fetch_recent_data(self, user_id: str) -> Dict[str, Any]:
        """
        Mocks a connection fetching recent ECG or PPG data.
        Returns normalized internal data structure.
        """
        # Generate some synthetic waveform data for testing
        waveform = [random.uniform(-1, 1) for _ in range(187)]
        return {
            "source": "simulator",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "avg_bpm": random.randint(60, 100),
            "sdrr_ms": random.uniform(40, 100),
            "rmssd_ms": random.uniform(20, 80),
            "waveform": waveform
        }

class ConnectionService:
    def __init__(self):
        self.simulator = SimulatorConnection()

    def sync_data(self, user_id: str, provider: str = "simulator") -> Dict[str, Any]:
        return self.simulator.fetch_recent_data(user_id)

connection_service_instance = ConnectionService()

def get_connection_service() -> ConnectionService:
    return connection_service_instance

from datetime import datetime, UTC
from typing import Dict, Any

class SilviaRealityLayer:
    """
    SILVIA Sensor Reality Layer.
    Ingests satellite, buoy, and IoT sensor data for a real-time truth feed.
    """
    def __init__(self):
        self.sensor_state = {}

    def ingest_sensor_data(self, source: str, data: Dict[str, Any]):
        self.sensor_state[source] = {
            "data": data,
            "timestamp": datetime.now(UTC)
        }
        return True

    def get_truth_feed(self):
        return self.sensor_state

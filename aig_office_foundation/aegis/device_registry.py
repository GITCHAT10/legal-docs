import uuid
from datetime import datetime, UTC
from typing import Dict, Optional

class DeviceRegistry:
    def __init__(self):
        self.devices = {} # device_id -> {identity_id, fingerprint, status}

    def register_device(self, identity_id: str, fingerprint: str) -> str:
        device_id = str(uuid.uuid4())
        self.devices[device_id] = {
            "identity_id": identity_id,
            "fingerprint": fingerprint,
            "status": "TRUSTED",
            "registered_at": datetime.now(UTC).isoformat()
        }
        return device_id

    def verify_device_binding(self, device_id: str, identity_id: str) -> bool:
        device = self.devices.get(device_id)
        return device is not None and device["identity_id"] == identity_id and device["status"] == "TRUSTED"

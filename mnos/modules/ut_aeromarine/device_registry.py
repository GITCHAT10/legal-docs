from typing import Dict, Optional

class DeviceRegistry:
    """
    UT AEROMARINE Device Registry.
    Tracks all authorized hybrid air-sea assets.
    """
    def __init__(self, shadow):
        self.shadow = shadow
        self.devices: Dict[str, dict] = {}

    def register_device(self, device_id: str, asset_info: dict):
        self.devices[device_id] = {
            "device_id": device_id,
            "asset_info": asset_info,
            "status": "ACTIVE"
        }
        # In a real system, this would be a SHADOW commit
        return True

    def is_device_ready(self, device_id: str) -> bool:
        device = self.devices.get(device_id)
        return device is not None and device.get("status") == "ACTIVE"

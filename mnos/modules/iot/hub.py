from typing import Dict, Any, Optional
from mnos.modules.iot.models import MarsDeviceSchema, MarsProtocol

class MarsEdgeHub:
    """
    MARS EDGE HUB: Local device controller and protocol-agnostic bridge.
    Local-first architecture.
    """
    def __init__(self, registry, event_bus, shadow_logger):
        self.registry = registry
        self.event_bus = event_bus
        self.shadow_logger = shadow_logger
        self.adapters = {} # Future: matter_adapter, mqtt_adapter

    def dispatch_command(self, device_id: str, command: str, payload: Any):
        """
        Routes commands to devices based on protocol.
        """
        device = self.registry.get_device(device_id)
        if not device: return {"error": "Device not found"}

        print(f"📡 MARS EDGE HUB: Dispatching {command} to {device.id} via {device.protocol}")

        # Log to SHADOW
        self.shadow_logger.log("MARS_HUB_DISPATCH", {"device_id": device_id, "command": command})

        # Emit EVENT
        self.event_bus.emit(f"MARS_HUB_CMD_{device_id}", {"command": command, "payload": payload})

        return {"status": "SUCCESS"}

    def get_topic_map(self, location: str, device_id: str) -> str:
        return f"mnos/mars/{location}/{device_id}"

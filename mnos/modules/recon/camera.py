from typing import Dict, Any, List
from mnos.modules.recon.threat import MarsSecurityEvent

class MarsCameraEventModel:
    """
    Unified Camera Event Model.
    """
    def __init__(self, event_bus, shadow_logger):
        self.event_bus = event_bus
        self.shadow_logger = shadow_logger

    def trigger_alert(self, camera_id: str, location: str, alert_type: str):
        event = MarsSecurityEvent(
            event_type="CAMERA_ALERT",
            source_id=camera_id,
            location=location,
            severity="HIGH"
        )
        # Log to SHADOW
        self.shadow_logger.log("MARS_CAMERA_ALERT", event.model_dump())
        # Emit to EVENTS
        self.event_bus.emit("MARS_SECURITY_ALERT", event.model_dump())
        return event

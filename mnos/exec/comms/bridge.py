import uuid
from datetime import datetime, UTC
from typing import Dict, Any

class SovereignBridge:
    """
    Sovereign Connector Bridge: Translates External World signals into MAC EOS events.
    Handles IoT (MQTT/Homey) and Webhooks (Zapier/Make).
    """
    def __init__(self, events, guard, shadow):
        self.events = events
        self.guard = guard
        self.shadow = shadow

    def ingest_iot_event(self, device_id: str, payload: dict) -> str:
        """
        Translates raw IoT signals (e.g., sensor data) into verified MAC EOS events.
        """
        trace_id = f"IOT-{uuid.uuid4().hex[:6].upper()}"

        # 1. Normalize
        mac_event_type = self._map_iot_type(payload.get("raw_type"))

        # 2. Verify and Commit
        with self.guard.sovereign_context(trace_id=trace_id):
            event_data = {
                "device_id": device_id,
                "data": payload.get("data"),
                "source": "SOVEREIGN_IOT_BRIDGE"
            }
            self.events.publish(mac_event_type, event_data)
            self.shadow.commit("bridge.iot.ingested", device_id, {"trace_id": trace_id, "type": mac_event_type})

        return trace_id

    def process_external_webhook(self, source: str, payload: dict) -> str:
        """
        Ingests data from external SaaS (e.g., OTA booking, HR update).
        """
        trace_id = f"WEBHOOK-{uuid.uuid4().hex[:6].upper()}"

        with self.guard.sovereign_context(trace_id=trace_id):
            normalized_payload = {
                "external_source": source,
                "payload": payload,
                "ingested_at": datetime.now(UTC).isoformat()
            }
            self.events.publish("external.webhook.received", normalized_payload)
            self.shadow.commit("bridge.webhook.processed", source, {"trace_id": trace_id})

        return trace_id

    def _map_iot_type(self, raw_type: str) -> str:
        mapping = {
            "motion": "GUEST_PRESENCE_DETECTED",
            "lock_unlock": "DOOR_ACCESS_GRANTED",
            "temp_change": "HVAC_ADJUSTMENT"
        }
        return mapping.get(raw_type, "BRIDGE_GENERIC_SIGNAL")

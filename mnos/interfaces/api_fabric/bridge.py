import uuid
from datetime import datetime, UTC
from typing import Dict, Any

class InterfaceBridge:
    """
    SOVEREIGN API FABRIC (PHASE 1): Core Signal Bridge.
    Connects primary systems (OTA, UT Mobility, POS) into MAC EOS EVENTS.
    """
    def __init__(self, events, guard, shadow):
        self.events = events
        self.guard = guard
        self.shadow = shadow

    def bridge_signal(self, source: str, signal_type: str, payload: dict) -> dict:
        """
        Normalize and inject signal into the sovereign execution core.
        """
        trace_id = f"BRG-{uuid.uuid4().hex[:6].upper()}"

        with self.guard.sovereign_context(trace_id=trace_id):
            normalized_event = {
                "source_system": source,
                "signal": signal_type,
                "data": payload,
                "ingested_at": datetime.now(UTC).isoformat(),
                "fabric_trace_id": trace_id
            }

            # Map signal to MAC EOS event type
            mac_event = self._map_to_mac_event(signal_type)
            self.events.publish(mac_event, normalized_event)
            self.shadow.commit("fabric.signal.ingested", source, {"signal": signal_type, "trace_id": trace_id})

        return {"trace_id": trace_id, "mac_event": mac_event, "status": "INGESTED"}

    def _map_to_mac_event(self, signal_type: str) -> str:
        # Phase 1: Focus on mission-critical economic signals
        mapping = {
            "ota_booking": "DMC.BOOKING_RECEIVED",
            "vessel_docked": "UT.VESSEL_ARRIVED",
            "pos_transaction": "UPOS.SALE_COMPLETED"
        }
        return mapping.get(signal_type, "FABRIC.GENERIC_SIGNAL")

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Callable
from mnos.modules.shadow.service import shadow

class EventBus:
    """
    MNOS Orchestration Core: Manages event lifecycle and n8n bridge.
    Ensures routing through SHADOW for immutable evidence.
    """
    TAXONOMY = {
        "nexus.booking.created",
        "nexus.guest.arrival",
        "nexus.payment.received",
        "nexus.emergency.triggered",
        "exmail.received",
        "exmail.sent",
        "exmail.task.created",
        "exmail.ticket.created",
        "network_routing_change",
        "system_shutdown",
        "data_purge",
        "ucloud.store",
        "ut.booking.created",
        "ut.cargo.dispatch",
        "ut.payout.finalized"
    }

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {event: [] for event in self.TAXONOMY}

    def publish(self, event_type: str, data: Dict[str, Any], trace_id: str = None) -> Dict[str, Any]:
        """Publishes an event and commits to SHADOW ledger."""
        if event_type not in self.TAXONOMY:
            raise ValueError(f"Unknown event type: {event_type}")

        if not trace_id:
            trace_id = str(uuid.uuid4())

        payload = {
            "event_id": str(uuid.uuid4()),
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }

        # Doctrine: n8n → MNOS EVENTS → AEGIS → FCE → SHADOW
        # All events MUST be recorded in SHADOW for sovereign truth
        shadow.commit(event_type, payload)

        # Trigger subscribers
        for callback in self.subscribers.get(event_type, []):
            try:
                callback(payload)
            except Exception as e:
                print(f"!!! EVENT SUBSCRIBER FAILURE: {str(e)} !!!")
                # We log but continue, the truth is already in SHADOW

        return payload

    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self.TAXONOMY:
            raise ValueError(f"Unknown event type: {event_type}")
        self.subscribers[event_type].append(callback)

events = EventBus()

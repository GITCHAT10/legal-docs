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
        "nexus.pio.ingest.folio",
        "nexus.pio.ingest.pos",
        "nexus.pio.ingest.inventory"
    }

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {event: [] for event in self.TAXONOMY}

    def publish(self, event_type: str, data: Dict[str, Any], trace_id: str = None) -> Dict[str, Any]:
        """Publishes an event and commits to SHADOW ledger."""
        # Enforce MIG EVENT LAW (Singularity Core)
        from mnos.infrastructure.mig_event_spine.service import event_spine
        event_spine.enforce_event_law(event_type, data)

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
        shadow.commit(
            event_type,
            payload,
            actor_id=data.get("actor_id", "SYSTEM"),
            objective_code=data.get("objective_code", "GENERIC")
        )

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

    def register_taxonomy(self, event_types: List[str]):
        """Allows modules to register new event types safely."""
        for et in event_types:
            if et not in self.TAXONOMY:
                self.TAXONOMY.add(et)
                self.subscribers[et] = []

events = EventBus()

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Callable
from mnos.modules.aig_shadow.service import aig_shadow

class EventBus:
    """
    MNOS Orchestration Core: Manages event lifecycle and n8n bridge.
    Ensures routing through AIGShadow for immutable evidence.
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
        "aig_vault.store",
        "ut.booking.created",
        "ut.cargo.dispatch",
        "ut.payout.finalized",
        "payment.received",
        "sala.invoice.finalized",
        "sala.guest.checkin",
        "sala.folio.updated",
        "nexus.guest.created",
        "nexus.reservation.confirmed",
        "FINALIZE_INVOICE_PROCESS",
        "apollo.deploy",
        "SYSTEM_OVERRIDE",
        "hms.rfq.outbound",
        "hms.quotes.read",
        "airlock.request_accepted",
        "airlock.request_blocked",
        "test"
    }

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {event: [] for event in self.TAXONOMY}

    def publish(self, event_type: str, data: Dict[str, Any], trace_id: str = None) -> Dict[str, Any]:
        """
        Publishes an event and commits to AIGShadow ledger.
        MIG EVENT LAW (FORTRESS BUILD):
        1. Blocks direct publish outside ExecutionGuard context.
        2. Prohibits raw event emission.
        3. Enforces trace_id persistence.
        """
        from mnos.shared.guard.service import in_sovereign_context, current_trace_id
        if not in_sovereign_context.get():
            raise RuntimeError("EVENT_SPINE: Direct publish blocked. Operation must go through ExecutionGuard.")

        if event_type not in self.TAXONOMY:
            raise ValueError(f"Unknown event type: {event_type}")

        # In MNOS 10.0, we reject events without a valid trace_id
        # ensuring everything is part of a guarded chain.
        trace_id = trace_id or current_trace_id.get()
        if not trace_id:
            raise RuntimeError("EVENT_SPINE: Trace_id is mandatory for all sovereign events.")

        payload = {
            "event_id": str(uuid.uuid4()),
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }

        # Doctrine: n8n → MNOS EVENTS → AIGAegis → FCE → AIGShadow
        # All events MUST be recorded in AIGShadow for sovereign truth
        aig_shadow.commit(event_type, payload)

        # Trigger subscribers
        for callback in self.subscribers.get(event_type, []):
            try:
                callback(payload)
            except Exception as e:
                print(f"!!! EVENT SUBSCRIBER FAILURE: {str(e)} !!!")
                # We log but continue, the truth is already in AIGShadow

        return payload

    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self.TAXONOMY:
            raise ValueError(f"Unknown event type: {event_type}")
        self.subscribers[event_type].append(callback)

events = EventBus()

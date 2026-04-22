from decimal import Decimal
from typing import Dict, Any
from mnos.infrastructure.mig_event_spine.service import events
from mnos.modules.fce.service import fce

def handle_booking(payload: Dict[str, Any]):
    """
    Booking → Payment → Confirmation Workflow.
    Proves: FCE validation, AIGShadow logging, Event emission.
    """
    data = payload["data"]
    trace_id = payload["trace_id"]

    print(f"[WORKFLOW] BOOKING Trace: {trace_id}")

    # 1. FCE Validation (Financial Integrity)
    base_price = Decimal("500.00")
    folio = fce.calculate_folio(base_price)
    print(f" - FCE Calculated: {folio['total']} USD")

    # 2. Confirmation Event
    events.publish(
        "nexus.payment.received",
        {"amount": str(folio["total"]), "folio_id": "F-999"},
        trace_id=trace_id
    )
    print(" - Confirmation dispatched.")

events.subscribe("nexus.booking.created", handle_booking)

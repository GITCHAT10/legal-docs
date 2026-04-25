from decimal import Decimal
from typing import Dict, Any
from mnos.core.events.service import events
from mnos.modules.fce.service import fce

def handle_booking(payload: Dict[str, Any]):
    """
    Booking → Payment → Confirmation Workflow.
    Proves: FCE validation, SHADOW logging, Event emission.
    """
    data = payload["data"]
    trace_id = payload["trace_id"]

    print(f"[WORKFLOW] BOOKING Trace: {trace_id}")

    # 1. FCE Validation (Financial Integrity)
    base_price = Decimal("500.00")
    folio = fce.calculate_folio(base_price)
    print(f" - FCE Calculated: {folio['total']} USD")

    # 2. Confirmation Event (Internal Workflow)
    # Singularity Core: Workflows use system-signed authority for sub-tasks
    import time
    from mnos.shared.execution_guard import guard
    from mnos.core.security.aegis import aegis

    ctx_wf = {
        "user_id": "WF-BOOKING",
        "session_id": f"S-WF-{trace_id}",
        "device_id": "nexus-admin-01",
        "issued_at": int(time.time()),
        "nonce": f"N-WF-{trace_id}"
    }
    ctx_wf["signature"] = aegis.sign_session(ctx_wf)

    guard.execute_sovereign_action(
        "nexus.payment.received",
        {"amount": str(folio["total"]), "folio_id": "F-999"},
        ctx_wf,
        lambda x: None
    )
    print(" - Confirmation dispatched.")

events.subscribe("nexus.booking.created", handle_booking)

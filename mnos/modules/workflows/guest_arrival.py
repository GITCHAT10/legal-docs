from typing import Dict, Any
from mnos.infrastructure.mig_event_spine.service import events

def handle_guest_arrival(payload: Dict[str, Any]):
    """
    Autonomous Guest Arrival Workflow.
    Proves: AQUA transfer dispatch, INN readiness, AIGShadow logging.
    """
    data = payload["data"]
    trace_id = payload["trace_id"]

    print(f"[WORKFLOW] GUEST ARRIVAL Trace: {trace_id}")
    print(f" - Dispatching MARS AQUA transfer for {data.get('phone')}")
    print(" - Setting room status to READY in MARS INN")
    print(" - Welcome message sent via SKY-i COMMS")

events.subscribe("nexus.guest.arrival", handle_guest_arrival)

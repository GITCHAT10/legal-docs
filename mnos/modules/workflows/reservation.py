from typing import Dict, Any
from mnos.infrastructure.mig_event_spine.service import events
from mnos.shared.guard.service import guard

class ReservationWorkflow:
    """
    SALA Reservation Workflow: Processes bookings into guest records and confirmed reservations.
    """
    def __init__(self):
        events.subscribe("nexus.booking.created", self.handle_booking)

    def handle_booking(self, payload: Dict[str, Any]):
        """
        Orchestrates guest record and reservation creation upon booking.
        """
        data = payload.get("data", {})
        trace_id = payload.get("trace_id")

        # Scenario: Create Guest Record
        guest_id = f"G-{data.get('guest_name', 'UNK')[:3].upper()}"
        events.publish("nexus.guest.created", {
            "guest_id": guest_id,
            "guest_name": data.get("guest_name"),
            "trace_id": trace_id
        }, trace_id=trace_id)

        # Scenario: Create Reservation Record
        res_id = f"R-{trace_id[:6].upper()}"
        events.publish("nexus.reservation.confirmed", {
            "reservation_id": res_id,
            "guest_id": guest_id,
            "status": "CONFIRMED",
            "trace_id": trace_id
        }, trace_id=trace_id)

        # Trigger UT Provisioning
        events.publish("ut.booking.created", {
            "customer_id": guest_id,
            "reservation_id": res_id,
            "amount": "150.00",
            "trace_id": trace_id
        }, trace_id=trace_id)

reservation_workflow = ReservationWorkflow()

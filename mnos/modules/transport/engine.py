import uuid
from datetime import datetime, UTC

class TransportEngine:
    def __init__(self, core):
        self.core = core
        self.manifests = {}

    def book_transport(self, actor_ctx: dict, route_data: dict):
        return self.core.execute_commerce_action(
            "transport.booking.create",
            actor_ctx,
            self._internal_book,
            route_data
        )

    def _internal_book(self, data):
        # Fare calculation
        fare = data.get("fare", 0)
        split = {
            "fare": fare,
            "operator_cut": fare * 0.9,
            "platform_fee": fare * 0.1
        }
        booking = {
            "ticket_id": f"TR-{uuid.uuid4().hex[:6].upper()}",
            "route": data.get("route"),
            "passenger_id": (self.core.guard.get_actor() or {}).get("identity_id", "SYSTEM"),
            "split": split,
            "status": "BOARDING_READY"
        }
        from mnos.shared.execution_guard import set_system_context, _sovereign_context
        token = None
        if _sovereign_context.get() is None:
            set_system_context()
            token = "INTERNAL"
        try:
            self.core.events.publish("transport.manifest_updated", booking)
        finally:
            if token:
                _sovereign_context.set(None)
        return booking

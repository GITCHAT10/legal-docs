import uuid

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
            "passenger_id": self.core.guard.get_actor().get("identity_id"),
            "split": split,
            "status": "BOARDING_READY"
        }
        self.core.events.publish("transport.manifest_updated", booking)
        return booking

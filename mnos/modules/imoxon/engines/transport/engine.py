class TransportEngine:
    def __init__(self, guard, fce, shadow, events):
        self.guard = guard
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def book_journey(self, actor_ctx: dict, booking_data: dict):
        return self.guard.execute_sovereign_action(
            "imoxon.transport.book",
            actor_ctx,
            self._internal_book_journey,
            booking_data
        )

    def _internal_book_journey(self, booking_data: dict):
        base_fare = booking_data.get("fare", 0)
        pricing = self.fce.price_order(base_fare)

        # Transport Split: 85% to driver, 15% platform
        split = self.fce.calculate_isky_split(Decimal(str(pricing["total"])))

        entry = {
            "passenger": self.guard.get_actor().get("identity_id"),
            "route": booking_data.get("route"),
            "pricing": pricing,
            "split": split,
            "status": "BOOKED"
        }
        self.events.publish("transport.booked", entry)
        return entry
from decimal import Decimal

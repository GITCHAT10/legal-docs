class TourismEngine:
    def __init__(self, guard, fce, shadow, events):
        self.guard = guard
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def book_package(self, actor_ctx: dict, booking_data: dict):
        return self.guard.execute_sovereign_action(
            "imoxon.tourism.book",
            actor_ctx,
            self._internal_book_package,
            booking_data
        )

    def _internal_book_package(self, data: dict):
        base_price = data.get("price", 0)
        # Tourism requires 17% TGST
        pricing = self.fce.finalize_invoice(base_price, "TOURISM")

        entry = {
            "guest": self.guard.get_actor().get("identity_id"),
            "package": data.get("package_id"),
            "pricing": pricing,
            "status": "BOOKED"
        }
        self.events.publish("tourism.booked", entry)
        return entry

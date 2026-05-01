import uuid
from datetime import datetime, UTC

class TourismEngine:
    def __init__(self, core):
        self.core = core
        self.bookings = {}

    def book_package(self, actor_ctx: dict, package_data: dict):
        return self.core.execute_commerce_action(
            "tourism.booking.create",
            actor_ctx,
            self._internal_book,
            package_data
        )

    def _internal_book(self, data):
        pricing = self.core.fce.finalize_invoice(data.get("price"), "TOURISM")
        booking = {
            "booking_id": f"T-BK-{uuid.uuid4().hex[:6].upper()}",
            "package_id": data.get("package_id"),
            "customer_id": self.core.guard.get_actor().get("identity_id"),
            "pricing": pricing,
            "status": "CONFIRMED"
        }
        self.core.events.publish("tourism.booking_confirmed", booking)
        return booking

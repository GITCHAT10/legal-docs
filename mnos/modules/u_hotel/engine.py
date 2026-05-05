import uuid

class UHotelEngine:
    """
    U-Hotel Vertical: Room, folio, and guest stay commerce.
    """
    def __init__(self, upos):
        self.upos = upos
        self.properties = {}
        self.bookings = {}

    def register_property(self, actor_ctx: dict, property_data: dict):
        return self.upos.execute_transaction(
            "hospitality.property.register",
            actor_ctx,
            self._internal_register,
            property_data
        )

    def _internal_register(self, data):
        prop_id = f"HOTEL-{uuid.uuid4().hex[:6].upper()}"
        property_entry = {
            "id": prop_id,
            "name": data.get("name"),
            "location": data.get("location"),
            "base_rate": data.get("base_rate"),
            "type": data.get("type", "HOTEL")
        }
        self.properties[prop_id] = property_entry
        return property_entry

    def book_stay(self, actor_ctx: dict, booking_data: dict):
        return self.upos.execute_transaction(
            "upos.order.create",
            actor_ctx,
            self._internal_book,
            booking_data,
            actor_ctx
        )

    def _internal_book(self, data, actor_ctx):
        prop_id = data.get("property_id")
        prop = self.properties.get(prop_id)
        if not prop:
            raise ValueError("Property not found")

        # Use UPOS for order creation
        order = self.upos._internal_create_order(
            {"amount": prop["base_rate"] * data.get("nights", 1), "tenant_id": prop_id},
            "TOURISM"
        )

        booking = {
            "booking_id": f"BK-{uuid.uuid4().hex[:6].upper()}",
            "order_id": order["id"],
            "property_id": prop_id,
            "status": "CONFIRMED"
        }
        self.bookings[booking["booking_id"]] = booking
        return booking

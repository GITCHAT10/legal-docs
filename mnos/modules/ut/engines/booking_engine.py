import uuid
from typing import Dict, Any, List
from datetime import datetime, UTC

class UTBookingEngine:
    def __init__(self, core, fce_split):
        self.core = core
        self.fce_split = fce_split
        self.bookings = {}

    def create_intent(self, actor_ctx: dict, journey_data: dict):
        """
        Initializes a transfer intent. Requires trace_id.
        """
        trace_id = journey_data.get("trace_id")
        if not trace_id:
            raise ValueError("NO_TRACE_ID_NO_TRANSFER: Trace ID is mandatory")

        return self.core.execute_commerce_action(
            "ut.booking.intent",
            actor_ctx,
            self._internal_intent,
            journey_data
        )

    def _internal_intent(self, data):
        booking_id = f"UT-{uuid.uuid4().hex[:6].upper()}"
        trace_id = data["trace_id"]

        # Create Quote
        base_amount = data.get("amount", 0)
        category = data.get("category", "TRANSPORT")
        is_public = data.get("is_public", False)

        quote = self.fce_split.create_quote(trace_id, base_amount, category, is_public)

        intent = {
            "booking_id": booking_id,
            "trace_id": trace_id,
            "quote": quote,
            "status": "INTENT_CREATED",
            "created_at": datetime.now(UTC).isoformat()
        }
        self.bookings[booking_id] = intent
        self.core.events.publish("ut.booking_intent_created", intent)
        return intent

    def confirm_booking(self, actor_ctx: dict, booking_id: str):
        """
        Confirms booking and locks price.
        """
        return self.core.execute_commerce_action(
            "ut.booking.confirm",
            actor_ctx,
            self._internal_confirm,
            booking_id
        )

    def _internal_confirm(self, booking_id):
        booking = self.bookings.get(booking_id)
        if not booking:
            raise ValueError("Booking not found")

        booking["status"] = "CONFIRMED"
        booking["quote"]["is_locked"] = True

        # Prepare splits
        splits = self.fce_split.prepare_split(booking["quote"]["quote_id"])
        booking["splits"] = splits

        self.core.events.publish("ut.booking_confirmed", booking)
        return booking

    def get_manifest(self, actor_ctx: dict, booking_id: str):
        """
        Role-scoped manifest access.
        """
        booking = self.bookings.get(booking_id)
        role = actor_ctx.get("role")

        if role not in ["SUPPLIER_ADMIN", "CAPTAIN_DRIVER", "UT_COMMAND"]:
             # P3/P4 Privacy Masking for non-operators
             return {"message": "PRIVACY_MASKING_ACTIVE", "data": "PROTECTED"}

        return booking

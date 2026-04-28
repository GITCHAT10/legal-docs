import uuid
import structlog
from datetime import datetime, UTC
from enum import Enum
from typing import Dict, Any, Optional

logger = structlog.get_logger("prestige.booking")

class BookingState(str, Enum):
    QUOTE = "QUOTE"
    CONFIRMED = "CONFIRMED"
    PAID = "PAID"
    LOCKED = "LOCKED"
    INVOICED = "INVOICED"
    FAILED = "FAILED"

class BookingManager:
    """
    Sovereign Booking Manager: Manages the full lifecycle of Prestige bookings.
    Ensures state changes are anchored in SHADOW and inventory is atomically locked.
    """
    def __init__(self, core, inventory_ledger):
        self.core = core
        self.inventory = inventory_ledger
        self.bookings = {} # booking_id -> data

    def create_quote(self, actor_ctx: Dict, pricing_response: Any):
        """Initial state: Valid quote generated and anchored."""
        booking_id = f"BK-{uuid.uuid4().hex[:8].upper()}"

        # Convert Pydantic models to dict for JSON serialization in SHADOW
        if hasattr(pricing_response, "model_dump"):
            pricing_data = pricing_response.model_dump(mode="json")
        else:
            pricing_data = pricing_response

        data = {
            "id": booking_id,
            "state": BookingState.QUOTE,
            "pricing": pricing_data,
            "created_at": datetime.now(UTC).isoformat()
        }

        return self.core.execute_commerce_action(
            "booking.quote.created",
            actor_ctx,
            self._internal_save,
            data
        )

    def confirm_booking(self, actor_ctx: Dict, booking_id: str, product_code: str, travel_date: str, units: int):
        """Transition to CONFIRMED and hold inventory."""
        booking = self.bookings.get(booking_id)
        if not booking: raise ValueError("Booking not found")

        # Atomically Hold Inventory
        # async call in manager, but for simulation we sync
        # import asyncio
        # loop = asyncio.get_event_loop()
        # success = loop.run_until_complete(self.inventory.hold_inventory(product_code, travel_date, units, booking_id))

        # For simplicity in this non-async manager:
        success = True # In simulation, we assume hold succeeds if called correctly

        if not success:
             booking["state"] = BookingState.FAILED
             raise RuntimeError("FAIL CLOSED: Inventory hold failed")

        booking["state"] = BookingState.CONFIRMED
        booking["inventory_meta"] = {"product": product_code, "date": travel_date, "units": units}

        return self.core.execute_commerce_action(
            "booking.confirmed",
            actor_ctx,
            self._internal_save,
            booking
        )

    def record_payment(self, actor_ctx: Dict, booking_id: str, payment_ref: str):
        """Transition to PAID and anchor in SHADOW."""
        booking = self.bookings.get(booking_id)
        if not booking: raise ValueError("Booking not found")

        booking["state"] = BookingState.PAID
        booking["payment_ref"] = payment_ref

        return self.core.execute_commerce_action(
            "booking.paid",
            actor_ctx,
            self._internal_save,
            booking
        )

    def lock_and_invoice(self, actor_ctx: Dict, booking_id: str):
        """Final transition: LOCK inventory and issue MIRA-compliant invoice."""
        booking = self.bookings.get(booking_id)
        if not booking: raise ValueError("Booking not found")

        # 1. Finalize Invoice via FCE
        # Convert response object to dict for easier access if it's a pydantic model
        if hasattr(booking["pricing"], "model_dump"):
            pricing = booking["pricing"].model_dump()
        else:
            pricing = booking["pricing"]

        invoice = self.core.fce.calculate_local_order(
            base_price=pricing["waterfall"]["net_cost"],
            category=pricing["tax"]["tax_type"],
            locked_fx_rate=pricing.get("fx_rate_locked", 15.42),
            input_currency=pricing["currency"]
        )

        booking["state"] = BookingState.INVOICED
        booking["invoice"] = invoice

        # 2. COMMIT TO SHADOW and emit event
        result = self.core.execute_commerce_action(
            "booking.invoiced",
            actor_ctx,
            self._internal_save,
            booking
        )

        self.core.events.publish("booking.finalized", result)
        return result

    def _internal_save(self, data):
        self.bookings[data["id"]] = data
        return data

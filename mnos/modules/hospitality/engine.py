import uuid
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
from decimal import Decimal

class LowCostHospitalityEngine:
    """
    Low-Cost & Transit Hospitality Engine for Maldives.
    Focuses on "no-frills" models (Tune/easyHotel/YOTEL style) with pay-as-you-use amenities.
    Integrates with specialized industry partner discounts.
    """
    def __init__(self, core):
        self.core = core
        self.properties = {}
        self.bookings = {}

        # Industry Role Discount Mapping
        self.role_discounts = {
            "airline_partner": 0.25, # 25% Off
            "medical_worker": 0.20,  # 20% Off
            "dmc_ta_staff": 0.15,    # 15% Off
            "club_member": 0.10      # 10% Off
        }

        # Pay-as-you-use amenities catalog
        self.amenities = {
            "aircon": 10.0,      # USD per night
            "tv": 5.0,           # USD per stay
            "wifi_premium": 5.0, # USD per day
            "towel_refresh": 2.0 # USD per use
        }

    def register_property(self, actor_ctx: dict, property_data: dict):
        return self.core.execute_commerce_action(
            "hospitality.property.register",
            actor_ctx,
            self._internal_register,
            property_data
        )

    def _internal_register(self, data):
        prop_id = f"HOS-{uuid.uuid4().hex[:6].upper()}"
        property_entry = {
            "id": prop_id,
            "name": data.get("name"),
            "location": data.get("location"),
            "base_rate": data.get("base_rate"), # In USD
            "type": data.get("type", "GUESTHOUSE"),
            "registered_at": datetime.now(UTC).isoformat()
        }
        self.properties[prop_id] = property_entry
        self.core.events.publish("hospitality.property_registered", property_entry)
        return property_entry

    def book_stay(self, actor_ctx: dict, booking_data: dict):
        """
        Main booking flow. Validates actor role for potential discounts.
        """
        # Determine if it's an industry discount booking for policy check
        action_type = "imoxon.order.create"
        if any(role in self.role_discounts for role in [actor_ctx.get("role")]):
             action_type = "industry_discount_booking"

        return self.core.execute_commerce_action(
            action_type,
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

        base_rate = Decimal(str(prop["base_rate"]))
        nights = Decimal(str(data.get("nights", 1)))

        # Calculate discount based on actor role
        role = actor_ctx.get("role")
        discount_pct = Decimal(str(self.role_discounts.get(role, 0)))
        discount_amount = base_rate * nights * discount_pct

        # Calculate amenities
        amenities_total = Decimal("0")
        selected_amenities = data.get("amenities", [])
        for am in selected_amenities:
            if am in self.amenities:
                amenities_total += Decimal(str(self.amenities[am]))

        subtotal_usd = (base_rate * nights) - discount_amount + amenities_total

        # Convert to MVR using FCE locked rate
        mvr_rate = self.core.fce.locked_rates.get("USD", Decimal("15.42"))
        subtotal_mvr = subtotal_usd * mvr_rate

        # Apply Maldives Taxes via FCE
        pricing = self.core.fce.calculate_local_order(subtotal_mvr, "TOURISM")

        booking = {
            "booking_id": f"BK-{uuid.uuid4().hex[:6].upper()}",
            "property_id": prop_id,
            "customer_id": actor_ctx.get("identity_id"),
            "nights": int(nights),
            "base_usd": float(base_rate),
            "discount_applied": float(discount_amount),
            "amenities_total": float(amenities_total),
            "pricing": pricing,
            "status": "CONFIRMED",
            "booked_at": datetime.now(UTC).isoformat()
        }

        self.bookings[booking["booking_id"]] = booking
        self.core.events.publish("hospitality.booking_confirmed", booking)
        return booking

    def get_properties(self):
        return list(self.properties.values())

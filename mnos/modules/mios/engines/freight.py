from uuid import UUID, uuid4
from decimal import Decimal
from typing import List, Dict, Optional
from mnos.modules.mios.schemas.models import FreightBooking, CargoDWS

class SkyFreightGDS:
    def __init__(self, shadow):
        self.shadow = shadow
        self.bookings: Dict[UUID, FreightBooking] = {}

        # Seed rates
        self.sea_lcl_rates = {
            "1-5": Decimal("147"),
            "5-10": Decimal("142"),
            "10+": Decimal("139")
        }
        self.bl_fee = Decimal("50")
        self.doc_fee = Decimal("36")

    def create_sea_booking(self, actor_ctx: dict, shipment_id: UUID, cbm: Decimal) -> FreightBooking:
        booking_id = uuid4()

        rate = self.sea_lcl_rates["1-5"]
        if 5 <= cbm < 10:
            rate = self.sea_lcl_rates["5-10"]
        elif cbm >= 10:
            rate = self.sea_lcl_rates["10+"]

        cost = (cbm * rate) + self.bl_fee + self.doc_fee

        booking = FreightBooking(
            id=booking_id,
            shipment_id=shipment_id,
            mode="SEA_LCL",
            cost_usd=cost,
            status="BOOKING_CONFIRMED"
        )
        self.bookings[booking_id] = booking
        self.shadow.commit("mios.freight.sea_booked", actor_ctx["identity_id"], booking.dict())
        return booking

    def calculate_air_cost(self, dws: CargoDWS) -> Decimal:
        min_charge = Decimal("130")
        chargeable_weight = dws.chargeable_weight_kg

        # Simple tiered rate
        rate = Decimal("6.94")
        if chargeable_weight >= 300:
            rate = Decimal("3.79")
        if chargeable_weight >= 1000:
            rate = Decimal("1.45")

        cost = chargeable_weight * rate
        return max(min_charge, cost)

class SkyParcelEngine:
    def __init__(self):
        self.rates = {
            "CN": {"base": 8, "per_kg": 3.50, "min": 12},
            "IN": {"base": 6, "per_kg": 3.00, "min": 10},
            "DXB": {"base": 10, "per_kg": 5.00, "min": 15},
            "TH": {"base": 8, "per_kg": 4.00, "min": 12}
        }

    def calculate_parcel_price(self, hub_code: str, dws: CargoDWS, priority: str = "STANDARD") -> Decimal:
        hub_rates = self.rates.get(hub_code)
        if not hub_rates:
            raise ValueError(f"Invalid hub code: {hub_code}")

        chargeable_weight = dws.chargeable_weight_kg
        subtotal = Decimal(str(hub_rates["base"])) + (chargeable_weight * Decimal(str(hub_rates["per_kg"])))
        price = max(subtotal, Decimal(str(hub_rates["min"])))

        multipliers = {"STANDARD": Decimal("1.00"), "PRIORITY": Decimal("1.25"), "URGENT": Decimal("1.50")}
        return price * multipliers.get(priority, Decimal("1.00"))

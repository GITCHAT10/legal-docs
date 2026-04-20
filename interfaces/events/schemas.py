from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, Any
from decimal import Decimal, ROUND_HALF_UP

def calculate_mira_tax(base_price: Decimal) -> Dict[str, Decimal]:
    """
    Maldives Finance Rule:
    Base Price + 10% Service Charge = Subtotal
    TGST = 17% of Subtotal
    Grand Total = Subtotal + TGST
    """
    service_charge = (base_price * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    subtotal = base_price + service_charge
    tgst = (subtotal * Decimal("0.17")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    grand_total = subtotal + tgst

    return {
        "base_price": base_price,
        "service_charge": service_charge,
        "subtotal": subtotal,
        "tgst": tgst,
        "grand_total": grand_total
    }

class TransportPreference(BaseModel):
    route_id: str
    vessel_preference: Optional[str] = "luxury_speed_ferry"
    departure_window: str
    return_required: bool = True

class BundleBookPayload(BaseModel):
    event_id: str
    transport: TransportPreference
    wallet_id: str
    insurance_opt_in: bool = True
    trace_id: str

class TicketOrderSchema(BaseModel):
    id: str
    event_id: str
    base_price: Decimal
    service_charge: Decimal
    tgst: Decimal
    grand_total: Decimal
    currency: str = "USD"
    status: str

    @model_validator(mode="after")
    def validate_tax_calculation(self) -> "TicketOrderSchema":
        expected = calculate_mira_tax(self.base_price)
        if self.service_charge != expected["service_charge"]:
            raise ValueError(f"Service charge mismatch. Expected {expected['service_charge']}, got {self.service_charge}")
        if self.tgst != expected["tgst"]:
            raise ValueError(f"TGST mismatch. Expected {expected['tgst']}, got {self.tgst}")
        if self.grand_total != expected["grand_total"]:
            raise ValueError(f"Grand total mismatch. Expected {expected['grand_total']}, got {self.grand_total}")
        return self

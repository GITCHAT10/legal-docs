from pydantic import BaseModel
from datetime import date
from typing import Optional, Dict, Any

class CanonicalBooking(BaseModel):
    """
    MAC EOS Canonical Booking Object: Proves operational truth from hospitality intent.
    """
    source_system: str
    source_channel: str
    external_reservation_id: str
    property_id: str
    establishment_id: str
    guest_ref: Optional[str] = None
    aegis_guest_id: Optional[str] = None
    arrival_date: date
    departure_date: date
    room_type: str
    room_category: str
    meal_plan: str
    occupancy: int
    base_rate: float
    currency: str = "MVR"
    tax_inclusive_or_exclusive: str = "EXCLUSIVE"
    service_charge_rate: float = 0.10
    tgst_rate: float = 0.17
    green_tax_applicable: bool = True
    transfer_required: bool = False
    payment_status: str = "UNPAID"
    booking_status: str = "DRAFT"
    market_scope: str = "PUBLIC"
    agent_scope: str = "NONE"
    privacy_scope: str = "BASE"
    trace_id: str
    shadow_refs: Dict[str, str] = {}
    metadata: Dict[str, Any] = {}

class BasePMSAdapter:
    """Base class for all PMS/HMS connectors."""
    def normalize(self, raw_data: Any) -> CanonicalBooking:
        raise NotImplementedError

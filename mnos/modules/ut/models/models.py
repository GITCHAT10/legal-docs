from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class UTBaseModel:
    def to_dict(self):
        return self.__dict__

@dataclass
class UTPartnerProfile(UTBaseModel):
    identity_id: str
    partner_type: str
    verified: bool = False

@dataclass
class UTVendor(UTBaseModel):
    vendor_id: str
    business_name: str
    kyc_status: str
    payout_profile_id: Optional[str] = None

@dataclass
class UTAsset(UTBaseModel):
    asset_id: str
    vendor_id: str
    template_id: str
    asset_type: str
    capacity: int
    status: str = "ACTIVE"

@dataclass
class UTRoute(UTBaseModel):
    route_id: str
    origin_node: str
    destination_node: str
    transport_mode: str
    is_active: bool = True

@dataclass
class UTJourneyLeg(UTBaseModel):
    leg_id: str
    journey_id: str
    route_id: str
    asset_id: str
    departure_time: datetime
    arrival_time: datetime
    leg_order: int
    status: str = "SCHEDULED"

@dataclass
class UTJourney(UTBaseModel):
    journey_id: str
    trace_id: str
    customer_id: str
    legs: List[UTJourneyLeg] = field(default_factory=list)
    status: str = "INTENT"
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class UTBooking(UTBaseModel):
    booking_id: str
    journey_id: str
    trace_id: str
    pricing_quote_id: str
    status: str = "PENDING"

@dataclass
class UTQuote(UTBaseModel):
    quote_id: str
    trace_id: str
    base_amount: float
    tax_amount: float
    service_charge: float
    esg_csr_fee: float
    total_amount: float
    is_locked: bool = False

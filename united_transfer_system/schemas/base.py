from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from united_transfer_system.models.base import LegType, JourneyStatus, PartnerTier

class LegBase(BaseModel):
    type: LegType
    origin: str
    destination: str
    departure_time: Optional[datetime] = None

class LegCreate(LegBase):
    pass

class Leg(BaseModel):
    id: int
    journey_id: int
    status: str
    master_voucher_code: str
    qr1_verified: bool
    qr2_verified: bool

    model_config = ConfigDict(from_attributes=True)

class JourneyCreate(BaseModel):
    tenant_id: str = "default"
    trace_id: str
    external_reference: Optional[str] = None
    legs: List[LegCreate]

class Journey(BaseModel):
    id: int
    tenant_id: str
    trace_id: str
    created_at: datetime
    external_reference: Optional[str]
    status: JourneyStatus
    legs: List[Leg]

    model_config = ConfigDict(from_attributes=True)

class TelemetryCreate(BaseModel):
    leg_id: int
    latitude: float
    longitude: float
    speed: Optional[float] = None
    heading: Optional[float] = None

class AvailabilityQuery(BaseModel):
    origin: str
    destination: str
    departure_date: datetime
    pax_count: int = 1

class HandshakeInput(BaseModel):
    leg_id: int
    scan_type: str # pickup or dropoff
    master_code: str
    actor_id: str
    actor_role: str

class PartnerCreate(BaseModel):
    name: str
    tier: PartnerTier = PartnerTier.STABILIZING

class TransferRequest(BaseModel):
    request_id: str
    actor_id: str
    origin: str
    destination: str
    time_window: datetime
    passengers: int
    priority: str = "NORMAL"

class AssetSync(BaseModel):
    name: str
    type: str
    capacity: int

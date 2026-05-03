from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class CargoDWS(BaseModel):
    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal
    actual_weight_kg: Decimal

    @property
    def actual_cbm(self) -> Decimal:
        return (self.length_cm * self.width_cm * self.height_cm) / Decimal("1000000")

    @property
    def volumetric_weight_kg(self) -> Decimal:
        return (self.length_cm * self.width_cm * self.height_cm) / Decimal("6000")

    @property
    def chargeable_weight_kg(self) -> Decimal:
        return max(self.actual_weight_kg, self.volumetric_weight_kg)

class CargoItem(BaseModel):
    id: UUID
    shipment_id: UUID
    description: str
    dws: CargoDWS
    cargo_lane: Optional[str] = "BLUE"
    parcel_eligible: bool = False
    qc_status: str = "PENDING"
    photo_proof_ids: List[str] = []

class Shipment(BaseModel):
    id: UUID
    customer_id: UUID
    origin_hub: str
    destination_hub: str = "MV"
    status: str = "CREATED"
    is_private_project_cargo: bool = False
    is_urgent_dispatch: bool = False
    landed_cost_locked: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

class Container(BaseModel):
    id: UUID
    container_no: Optional[str] = None
    hub_code: str
    type: str  # 20FT, 40HC
    capacity_cbm: Decimal
    status: str = "CONSOLIDATING"
    dispatch_reason: Optional[str] = None
    manifest_locked: bool = False

class FreightBooking(BaseModel):
    id: UUID
    shipment_id: UUID
    mode: str
    carrier_name: Optional[str] = None
    bl_awb_no: Optional[str] = None
    etd: Optional[datetime] = None
    eta: Optional[datetime] = None
    status: str = "QUOTE_REQUESTED"
    cost_usd: Decimal = Decimal("0")

class ClearingRecord(BaseModel):
    id: UUID
    shipment_id: UUID
    invoice_no: str
    invoice_total_usd: Decimal
    invoice_verified: bool = False
    hs_code: Optional[str] = None
    hs_code_confirmed: bool = False
    declaration_no: Optional[str] = None
    assessment_no: Optional[str] = None
    customs_payment_matched: bool = False
    port_release_verified: bool = False
    status: str = "DOCUMENTS_RECEIVED"

class FXRate(BaseModel):
    shipment_id: UUID
    source_currency: str
    target_currency: str
    rate_type: str
    rate: Decimal
    is_locked: bool = False

class FCELineItem(BaseModel):
    shipment_id: UUID
    category: str
    name: str
    amount_mvr: Decimal
    is_verified: bool = False

class AssetHandoff(BaseModel):
    id: UUID
    shipment_id: UUID
    handoff_type: str
    sender_id: UUID
    receiver_id: UUID
    condition_status: str = "GOOD"
    damage_flag: bool = False
    status: str = "PENDING"

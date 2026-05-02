from datetime import datetime, UTC
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import uuid

class ActorIdentityBundle(BaseModel):
    staff_id: str
    role_id: str
    device_id: str
    aegis_context_id: str
    session_hash: str
    geo_location: Optional[Dict[str, float]] = None # {"lat": 0.0, "lng": 0.0}

class FolioCharge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    folio_id: str
    charge_type: str # ROOM, FB, SPA, etc
    description: str
    quantity: int = 1
    unit_price: float
    subtotal: float
    service_charge_amount: float
    tgst_amount: float
    green_tax_amount: float
    line_total: float

    # MIRA Compliance: Green Tax specific
    green_tax_rate: float = 6.00 # USD
    green_tax_pax_count: int = 1
    green_tax_nights: int = 1
    green_tax_currency: str = "USD"

    # Audit: FX Locking
    fx_rate: float
    fx_source: str = "MVB_CENTRAL_BANK"
    fx_locked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Audit: Reversal
    reversal_of_charge_id: Optional[str] = None
    is_reversal: bool = False

    # Audit: Forensic Identity
    actor_identity: ActorIdentityBundle

    posted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self):
        data = self.model_dump()
        data["fx_locked_at"] = self.fx_locked_at.isoformat()
        data["posted_at"] = self.posted_at.isoformat()
        if self.actor_identity:
             data["actor_identity"] = self.actor_identity.model_dump()
        return data

class FolioPayment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    folio_id: str
    amount: float
    currency: str = "MVR"
    method: str # CASH, CARD, WALLET
    is_partial: bool = True
    settlement_sequence: int = 1

    # Audit: FX Locking
    fx_rate: float
    fx_source: str = "MVB_CENTRAL_BANK"
    fx_locked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    actor_identity: ActorIdentityBundle
    paid_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self):
        data = self.model_dump()
        data["fx_locked_at"] = self.fx_locked_at.isoformat()
        data["paid_at"] = self.paid_at.isoformat()
        if self.actor_identity:
             data["actor_identity"] = self.actor_identity.model_dump()
        return data

class Folio(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    guest_id: str
    reservation_id: Optional[str] = None
    status: str = "OPEN" # OPEN, SEALED, SETTLED, PARTIALLY_SETTLED, VOID
    currency: str = "MVR"

    # Balance Tracking
    total_amount: float = 0.0
    amount_paid: float = 0.0
    balance_due: float = 0.0
    green_tax_total: float = 0.0

    last_payment_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self):
        data = self.model_dump()
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.last_payment_at:
             data["last_payment_at"] = self.last_payment_at.isoformat()
        return data

class ChargeReversal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_charge_id: str
    reversal_charge_id: str
    reason_code: str # GUEST_COMPLAINT, SYSTEM_ERROR, STAFF_MISTAKE
    reason_detail: str
    approved_by: str # manager_id
    shadow_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self):
        data = self.model_dump()
        data["created_at"] = self.created_at.isoformat()
        return data

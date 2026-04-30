from pydantic import BaseModel, Field, field_validator, model_validator
from decimal import Decimal
from uuid import UUID
from enum import Enum
from datetime import date
from typing import Optional, Dict, Any

class TransferType(str, Enum):
    SPEEDBOAT = "speedboat"
    SEAPLANE = "seaplane"
    DOMESTIC = "domestic"
    CHARTER = "charter"
    BUS = "bus"

class VesselClass(str, Enum):
    STANDARD = "Standard"
    SEMI_LUXURY_AC = "Semi-Luxury_AC"
    LUXURY_YACHT = "Luxury_Yacht"

class TransferMode(str, Enum):
    COMBINED_SCHEDULED = "Combined_Scheduled"
    PRIVATE_CHARTER = "Private_Charter"

class TransferWay(str, Enum):
    ONE_WAY = "one_way"
    RETURN = "return"

class Currency(str, Enum):
    USD = "USD"
    MVR = "MVR"

class TaxContext(str, Enum):
    TOURISM_STANDARD = "TOURISM_STANDARD"
    TRANSPORT = "TRANSPORT"
    EXEMPT = "EXEMPT"

class ContractStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"

class TransferContract(BaseModel):
    transfer_contract_id: UUID
    supplier_id: UUID
    carrier_name: str
    vessel_class: Optional[VesselClass] = VesselClass.STANDARD
    transfer_mode: TransferMode = TransferMode.COMBINED_SCHEDULED
    sector: str
    route_from: str
    route_to: str
    transfer_type: TransferType
    one_way_or_return: TransferWay

    # Rates - must be positive/non-negative
    adult_rate: Decimal = Field(..., gt=0)
    child_rate: Decimal = Field(..., ge=0)
    infant_rate: Decimal = Field(..., ge=0)
    child_discount_pct: Optional[Decimal] = Field(None, ge=0, le=1)

    currency: Currency
    tax_context: TaxContext
    applicable_taxes: Dict[str, Any]

    # Luggage
    baggage_allowance_kg: int = 20
    hand_luggage_kg: int = 5
    is_unlimited_for_private: bool = True
    excess_baggage_rate: Decimal = Field(..., ge=0)

    # Rules
    # e.g. {"fuel_supplement_pct": 0.15, "night_transfer_surcharge": 50.0}
    fuel_surcharge_rule: Dict[str, Any]
    cancellation_rule: Dict[str, Any]
    refund_rule: Dict[str, Any]
    credit_terms: Dict[str, Any]

    # Deadlines (hours)
    manifest_deadline_hours: int
    ticketing_deadline_hours: int
    free_cancel_deadline_hours: int

    # Fees
    late_cancel_fee: Decimal = Field(..., ge=0)

    # Validity
    effective_from: date
    effective_to: date

    status: ContractStatus
    shadow_hash: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.effective_to < self.effective_from:
            raise ValueError("effective_to must be after effective_from")
        return self

from pydantic import BaseModel, Field
from decimal import Decimal
from uuid import UUID
from enum import Enum
from datetime import date
from typing import Optional, Dict, Any

class FeeCode(str, Enum):
    DPT = "DPT"
    ADF = "ADF"

class PassengerResidency(str, Enum):
    MALDIVIAN = "MALDIVIAN"
    FOREIGN = "FOREIGN"
    ANY = "ANY"

class TravelClass(str, Enum):
    ECONOMY = "ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"
    PRIVATE_JET = "PRIVATE_JET"

class CollectionResponsibility(str, Enum):
    AIRLINE = "AIRLINE"
    AIRPORT_OPERATOR = "AIRPORT_OPERATOR"

class RuleStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"

class AirportFeeRule(BaseModel):
    fee_rule_id: UUID
    fee_code: FeeCode
    fee_name: str
    applies_to_airport: Optional[str] = None
    applies_to_departure_country: str = "Maldives"
    passenger_residency: PassengerResidency
    travel_class: TravelClass
    amount_usd: Decimal = Field(..., ge=0)
    effective_from: date
    effective_to: Optional[date] = None
    collection_responsibility: CollectionResponsibility
    exemption_rule: Dict[str, Any]
    status: RuleStatus
    source_reference: str
    shadow_hash: Optional[str] = None

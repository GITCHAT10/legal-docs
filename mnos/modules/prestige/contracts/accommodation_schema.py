from pydantic import BaseModel, Field
from decimal import Decimal
from uuid import UUID
from enum import Enum
from datetime import date
from typing import Optional

class EstablishmentType(str, Enum):
    RESORT = "RESORT"
    INTEGRATED_RESORT = "INTEGRATED_RESORT"
    RESORT_HOTEL = "RESORT_HOTEL"
    CITY_HOTEL = "CITY_HOTEL"
    GUESTHOUSE = "GUESTHOUSE"
    SAFARI_VESSEL = "SAFARI_VESSEL"

class IslandType(str, Enum):
    PRIVATE_ISLAND = "PRIVATE_ISLAND"
    INHABITED_LOCAL_ISLAND = "INHABITED_LOCAL_ISLAND"
    UNINHABITED_ISLAND = "UNINHABITED_ISLAND"
    VESSEL = "VESSEL"

class MealPlan(str, Enum):
    RO = "RO"
    BB = "BB"
    HB = "HB"
    FB = "FB"
    AI = "AI"
    NON_ALCOHOLIC_AI = "NON_ALCOHOLIC_AI"

class AccommodationContractV2(BaseModel):
    contract_id: UUID
    supplier_id: UUID
    establishment_id: UUID
    establishment_type: EstablishmentType
    island_type: IslandType
    room_count: int

    # Rates
    base_rate: Decimal = Field(..., gt=0)
    currency: str = "USD"

    # Festive
    festive_gala_christmas: Optional[Decimal] = None
    festive_gala_new_year: Optional[Decimal] = None
    festive_tax_inclusive: bool = False

    # Compliance
    alcohol_allowed: bool = True
    split_stay_allowed: bool = True

    status: str = "active"
    effective_from: date
    effective_to: Optional[date] = None

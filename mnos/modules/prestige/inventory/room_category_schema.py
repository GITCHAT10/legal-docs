from pydantic import BaseModel, Field, model_validator
from decimal import Decimal
from uuid import UUID
from enum import Enum
from datetime import date
from typing import Optional, Dict, Any, Set

class RoomCategoryType(str, Enum):
    BEACH_VILLA = "BEACH_VILLA"
    WATER_VILLA = "WATER_VILLA"
    POOL_VILLA = "POOL_VILLA"
    FAMILY_VILLA = "FAMILY_VILLA"
    RESIDENCE = "RESIDENCE"
    OVERWATER_RESIDENCE = "OVERWATER_RESIDENCE"
    GARDEN_ROOM = "GARDEN_ROOM"
    CITY_ROOM = "CITY_ROOM"
    GUESTHOUSE_ROOM = "GUESTHOUSE_ROOM"
    SAFARI_CABIN = "SAFARI_CABIN"

class EstablishmentType(str, Enum):
    RESORT = "RESORT"
    INTEGRATED_RESORT = "INTEGRATED_RESORT"
    RESORT_HOTEL = "RESORT_HOTEL"
    CITY_HOTEL = "CITY_HOTEL"
    GUESTHOUSE = "GUESTHOUSE"
    SAFARI_VESSEL = "SAFARI_VESSEL"

class ViewType(str, Enum):
    BEACH = "BEACH"
    LAGOON = "LAGOON"
    OCEAN = "OCEAN"
    SUNSET = "SUNSET"
    SUNRISE = "SUNRISE"
    GARDEN = "GARDEN"
    CITY = "CITY"
    HARBOUR = "HARBOUR"
    INTERIOR = "INTERIOR"

class PrivacyLevel(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"

class TransferRequirement(str, Enum):
    SPEEDBOAT = "SPEEDBOAT"
    SEAPLANE = "SEAPLANE"
    DOMESTIC_PLUS_SPEEDBOAT = "DOMESTIC_PLUS_SPEEDBOAT"
    WALKING = "WALKING"
    CAR = "CAR"
    SAFARI_VESSEL = "SAFARI_VESSEL"

class InventorySource(str, Enum):
    DIRECT_CONTRACT = "DIRECT_CONTRACT"
    SALA = "SALA"
    TBO = "TBO"
    RATEHAWK = "RATEHAWK"
    HOTELBEDS = "HOTELBEDS"
    MANUAL_ALLOTMENT = "MANUAL_ALLOTMENT"

class RoomStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    STOP_SALE = "stop_sale"
    EXPIRED = "expired"
    SUSPENDED = "suspended"

class RoomCategory(BaseModel):
    room_category_id: UUID
    establishment_id: UUID
    supplier_id: UUID
    room_category_name: str
    room_category_type: RoomCategoryType
    establishment_type: EstablishmentType
    view_type: ViewType
    privacy_levels_supported: Set[PrivacyLevel]

    # Occupancy
    max_adults: int = Field(..., gt=0)
    max_children: int = Field(..., ge=0)
    max_infants: int = Field(..., ge=0)
    max_total_occupancy: int = Field(..., gt=0)
    base_occupancy: int = Field(..., gt=0)

    extra_adult_allowed: bool = False
    extra_child_allowed: bool = False
    extra_bed_allowed: bool = False
    extra_bed_rate: Decimal = Field(..., ge=0)

    child_rate_rule: Dict[str, Any]
    infant_policy: Dict[str, Any]
    meal_plan_allowed: Set[str]

    room_size_sqm: Optional[Decimal] = None
    bedroom_count: int = Field(..., ge=1)
    bathroom_count: int = Field(..., ge=1)

    # Amenities
    private_pool: bool = False
    direct_beach_access: bool = False
    overwater_access: bool = False
    wheelchair_accessible: bool = False
    smoking_allowed: bool = False
    connecting_room_available: bool = False

    transfer_requirement: TransferRequirement
    inventory_source: InventorySource
    allotment_count: int = Field(..., ge=0)
    release_period_days: int = Field(..., ge=0)
    stop_sale_flag: bool = False

    minimum_stay_nights: int = Field(1, ge=1)
    maximum_stay_nights: Optional[int] = None

    effective_from: date
    effective_to: Optional[date] = None

    status: RoomStatus
    shadow_hash: Optional[str] = None

    @model_validator(mode="after")
    def validate_occupancy(self):
        if self.max_total_occupancy < self.base_occupancy:
            raise ValueError("max_total_occupancy cannot be less than base_occupancy")
        return self

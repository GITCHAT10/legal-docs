from pydantic import BaseModel, Field
from typing import Optional, List

# --- Bucket A: Core ESG Schemas ---

class PMSInput(BaseModel):
    occupancy_rooms: int = Field(0, ge=0)
    laundry_volume_kg: float = Field(0, ge=0)
    fn_b_procurement_usd: float = Field(0, ge=0)

class LogisticsInput(BaseModel):
    speedboat_fuel_liters: float = Field(0, ge=0)
    staff_travel_km: float = Field(0, ge=0)
    guest_travel_km: float = Field(0, ge=0)

class EnvironmentalInput(BaseModel):
    electricity_kwh: float = Field(0, ge=0)
    water_m3: float = Field(0, ge=0)
    lpg_kg: float = Field(0, ge=0)
    plastic_waste_kg: float = Field(0, ge=0)
    recycled_waste_kg: float = Field(0, ge=0)
    coral_health_index: float = Field(0.0, ge=0.0, le=1.0) # 0 to 1 scale

class SocialInput(BaseModel):
    female_board_percent: float = Field(0.0, ge=0.0, le=100.0)
    local_supplier_spend_usd: float = Field(0.0, ge=0.0)
    community_project_spend_usd: float = Field(0.0, ge=0.0)

class GovernanceInput(BaseModel):
    sustainability_policy_active: bool = False
    internal_audit_score: float = Field(0.0, ge=0.0, le=100.0)

class FootprintInput(BaseModel):
    island_id: str = "MV-001"
    pms: Optional[PMSInput] = None
    logistics: Optional[LogisticsInput] = None
    environmental: Optional[EnvironmentalInput] = None
    social: Optional[SocialInput] = None
    governance: Optional[GovernanceInput] = None

class FootprintResult(BaseModel):
    home_total: float
    transport_total: float
    waste_total: float
    carbon_per_occupied_room: float
    grand_total: float
    shadow_hash: str
    compliance_status: str
    metrics: dict

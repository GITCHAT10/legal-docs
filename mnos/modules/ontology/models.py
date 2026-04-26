from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime

class GuestBioProfile(BaseModel):
    """
    MIG Foundry Ontology: Guest Bio-Profile.
    Integrates healthspan metrics with Sovereign ESG Regen Score.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    guest_id: str
    hrv_baseline: float
    sleep_efficiency: float
    cortisol_index: float

    # ESG Attributes
    regen_score: float = 0.0
    is_eco_sovereign: bool = False
    carbon_removed_kg: Decimal = Decimal("0.00")
    coral_regenerated_m2: float = 0.0

    # Metadata
    last_updated: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}

class CorporateBioTwin(BaseModel):
    """
    MIG Foundry Ontology: Corporate Bio-Twin.
    Maps corporate travel/HR entities to collective biological and ESG outcomes.
    """
    corporate_id: str
    employee_count: int
    collective_recovered_hours: float = 0.0
    longevity_dividend_accumulated: Decimal = Decimal("0.00")

    # ESG Aggregates
    total_social_dividend_usd: Decimal = Decimal("0.00")
    total_reef_restored_m2: float = 0.0

    active_itineraries: List[str] = []

class ReefHealth(BaseModel):
    """Archipelago Protocol: Ecosystem State."""
    location_id: str
    coral_cover_percentage: float
    bleaching_risk: float
    fish_biodiversity_index: float
    last_survey: datetime = Field(default_factory=datetime.now)

class CommunityWellbeing(BaseModel):
    """Archipelago Protocol: Social Sovereignty State."""
    island_id: str
    local_employment_rate: float
    health_access_index: float
    cultural_vitality_score: float
    fair_wage_compliance: bool = True

class CarbonBudget(BaseModel):
    """Archipelago Protocol: Sequestration State."""
    entity_id: str
    sequestration_capacity: float
    emission_allowance: float
    offset_quality_score: float

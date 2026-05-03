from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from uuid import UUID
from decimal import Decimal
from datetime import datetime

class AircraftSpecs(BaseModel):
    aircraft_type: str = "B737-700"
    passenger_cabin_type: str = "BUSINESS_ONLY"
    business_seats_total: int = Field(default=60, ge=60, le=72)
    belly_cargo_capacity_kg: Decimal = Decimal("3000")

class FlightRevenue(BaseModel):
    business_seats_sold: int
    average_business_fare: Decimal
    vip_group_revenue: Decimal = Decimal("0")
    vip_group_margin: Decimal = Decimal("0")
    corporate_block_revenue: Decimal = Decimal("0")
    prestige_package_margin: Decimal = Decimal("0")
    belly_cargo_booked_kg: Decimal
    cargo_yield_per_kg: Decimal
    priority_cargo_revenue: Decimal = Decimal("0")
    mios_cargo_margin: Decimal = Decimal("0")
    mios_route_service_margin: Decimal = Decimal("0")

    @property
    def business_passenger_revenue(self) -> Decimal:
        return self.business_seats_sold * self.average_business_fare

    @property
    def belly_cargo_revenue(self) -> Decimal:
        return self.belly_cargo_booked_kg * self.cargo_yield_per_kg

    @property
    def total_revenue(self) -> Decimal:
        return (
            self.business_passenger_revenue +
            self.vip_group_margin +
            self.belly_cargo_revenue +
            self.priority_cargo_revenue +
            self.mios_route_service_margin +
            self.prestige_package_margin
        )

class FlightCost(BaseModel):
    aircraft_charter_or_acmi_cost: Decimal
    airport_handling_cost: Decimal
    landing_navigation_parking_fees: Decimal = Decimal("0")
    fuel_surcharge: Decimal = Decimal("0")
    crew_positioning_cost: Decimal = Decimal("0")
    catering_cost: Decimal = Decimal("0")
    insurance_admin_cost: Decimal = Decimal("0")
    disruption_buffer: Decimal = Decimal("0")

    @property
    def total_cost(self) -> Decimal:
        return (
            self.aircraft_charter_or_acmi_cost +
            self.airport_handling_cost +
            self.landing_navigation_parking_fees +
            self.fuel_surcharge +
            self.crew_positioning_cost +
            self.catering_cost +
            self.insurance_admin_cost +
            self.disruption_buffer
        )

class AircraftDecision(BaseModel):
    id: UUID = Field(default_factory=datetime.now) # Using datetime as default factory for simplicity in MVP, but should be UUID
    route: str
    decision_mode: str
    business_load_factor: float
    cargo_utilization_pct: float
    coverage_ratio: float
    expected_profit: Decimal
    risk_flags: List[str] = []
    required_actions: List[str] = []
    approval_required_by: Optional[str] = None
    shadow_event_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class FlightData(BaseModel):
    route: str
    specs: AircraftSpecs
    revenue: FlightRevenue
    cost: FlightCost
    cargo_readiness_pct: float
    passenger_payment_collected_pct: float
    aircraft_quote_uploaded: bool
    ground_handling_confirmed: bool
    slot_or_route_permission_confirmed: bool
    weather_risk: str # LOW, MEDIUM, HIGH
    fce_cash_reserve_sufficient: bool
    route_risk_score: float
    historical_cycles_completed: int = 0
    average_historical_coverage_ratio: float = 0.0
    average_historical_load_factor: float = 0.0
    average_historical_cargo_utilization: float = 0.0
    forward_demand_months: int = 0
    cash_reserve_covers_downside: bool = False
    route_economics_stable: bool = False

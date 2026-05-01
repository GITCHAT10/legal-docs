from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, time

class SourceMarket(BaseModel):
    market_region: str
    origin_country: str
    origin_city: str
    origin_airport: str
    default_privacy: str = "P2"
    drivers: List[str] = []

class FlightConnectivityRecord(BaseModel):
    market_region: str
    origin_country: str
    origin_city: str
    origin_airport: str
    airline_code: str
    flight_number: str
    arrival_airport: str = "MLE"
    scheduled_arrival_time_mle: str # HH:MM format
    estimated_arrival_time_mle: Optional[str] = None
    arrival_day_pattern: List[str] = [] # ["MON", "WED"]
    seasonality: str = "YEAR_ROUND"
    average_delay_minutes: int = 0
    delay_risk_level: str = "LOW"
    baggage_risk: str = "LOW"
    weather_risk: str = "LOW"
    confidence_score: float = 1.0

class ResortClusterRecommendation(BaseModel):
    cluster_id: str
    resort_id: str
    resort_name: str
    destination_atoll: str
    transfer_mode: str # SEAPLANE, SPEEDBOAT, DOMESTIC_PLUS_SPEEDBOAT
    confidence_score: float = 1.0
    preferred_resort_cluster: str

class TransferFeasibilityProfile(BaseModel):
    resort_id: str
    transfer_mode: str
    seaplane_cutoff_time: str = "16:00"
    latest_safe_arrival_for_seaplane: str = "15:30"
    domestic_connection_required: bool = False
    last_domestic_flight_time: Optional[str] = None
    speedboat_feasible: bool = True
    night_speedboat_required: bool = False

class FlightDelayRiskProfile(BaseModel):
    flight_number: str
    risk_level: str
    average_delay_minutes: int

class MarketResortPreference(BaseModel):
    market_region: str
    preferred_clusters: List[str]

class RecoveryOption(BaseModel):
    template_id: str
    description: str
    night_1_stay: str
    day_2_transfer: str
    tone: str

class FlightMatrixDecision(BaseModel):
    trace_id: str
    feasibility_status: str # GREEN, YELLOW, RED, NEEDS_HUMAN_REVIEW, RECOVERY_REQUIRED
    risk_reason_codes: List[str] = []
    recovery_required: bool = False
    human_approval_required: bool = False
    safe_to_quote: bool = False
    safe_to_confirm: bool = False
    recovery_options: List[RecoveryOption] = []
    shadow_refs: List[str] = []

    # Input Context
    market_region: Optional[str] = None
    flight_number: Optional[str] = None
    resort_id: Optional[str] = None
    privacy_level: int = 2
    guest_segment: str = "STANDARD"
    baggage_estimate_kg: float = 0.0
    swell_height_m: float = 0.0
    overnight_male_risk: bool = False
    vip_cip_required: bool = False

class RecoveryWorkflowDecision(BaseModel):
    decision_id: str
    selected_template: str
    revised_proposal: Dict[str, Any]
    approvals_pending: List[str] = []
    shadow_seal: str

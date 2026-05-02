from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime
from .quote_status import QuoteStatus

class Source(BaseModel):
    platform: str
    campaign_id: str
    content_id: str
    user_handle: str

class GuestProfile(BaseModel):
    guest_name: str
    market: str
    country: str
    language: str
    whatsapp_e164: Optional[str] = None
    pdpa_sales_consent: bool

class TravelDates(BaseModel):
    check_in: str
    check_out: str
    nights: int
    date_flexibility: str = "fixed"

class Guests(BaseModel):
    adults: int
    children: int
    infants_under_2: int
    total_green_taxable_guests: int

    @validator("total_green_taxable_guests")
    def validate_green_taxable(cls, v, values):
        expected = values.get("adults", 0) + values.get("children", 0)
        if v != expected:
            raise ValueError(f"total_green_taxable_guests ({v}) must match adults + children ({expected})")
        return v

class StayPreference(BaseModel):
    resort_id: str
    resort_name: str
    room_category: str
    meal_plan: str
    special_occasion: Optional[str] = None

class Transfer(BaseModel):
    required: bool
    mode: str
    arrival_airport: str = "MLE"
    international_arrival_time: Optional[str] = None
    international_departure_time: Optional[str] = None

class BudgetSignal(BaseModel):
    original_currency: str
    original_amount: float
    usd_estimate: float
    note: str

class TripRequest(BaseModel):
    niche: str
    travel_dates: TravelDates
    guests: Guests
    stay_preference: StayPreference
    transfer: Transfer
    budget_signal: BudgetSignal

class GreenTaxRules(BaseModel):
    default_usd_per_taxable_guest_per_day: float = 12.0
    small_inhabited_island_guesthouse_usd_per_taxable_guest_per_day: float = 6.0
    children_under_2_exempt: bool = True

class PricingRules(BaseModel):
    service_charge_rate: float = 0.10
    tgst_rate: float = 0.17
    green_tax: GreenTaxRules = Field(default_factory=GreenTaxRules)
    prestige_margin_rule: str
    currency_output: List[str] = ["USD", "MVR"]
    fx_source: str = "approved_fce_fx_oracle"

class QuotePermissions(BaseModel):
    ai_can_send_to_guest: bool = False
    human_approval_required: bool = True
    allow_discount: bool = False
    allow_manual_override: bool = False

class QuoteRequest(BaseModel):
    request_id: str
    lead_id: str
    shadow_correlation_id: str
    source: Source
    guest_profile: GuestProfile
    trip_request: TripRequest
    pricing_rules: PricingRules
    quote_permissions: QuotePermissions

    @validator("pricing_rules")
    def validate_pricing_rules(cls, v):
        if v.tgst_rate != 0.17:
            raise ValueError("INVALID_TGST_RATE_2026: TGST must be 0.17")
        if v.service_charge_rate != 0.10:
            raise ValueError("Missing or invalid service charge rate")
        return v

    @validator("quote_permissions")
    def validate_permissions(cls, v):
        if v.ai_can_send_to_guest is not False:
            raise ValueError("AI_QUOTE_SEND_FORBIDDEN")
        if v.human_approval_required is not True:
            raise ValueError("Human approval must be required")
        return v

class GreenTaxBreakdown(BaseModel):
    rate_usd: float
    taxable_guests: int
    nights_or_days: int
    amount: float

class PriceBreakdown(BaseModel):
    base_contract_rate: float
    prestige_margin: float
    selling_base: float
    service_charge_10_percent: float
    taxable_subtotal: float
    tgst_17_percent: float
    green_tax: GreenTaxBreakdown
    transfer_fees: float
    total_guest_payable: float

class MVREquivalent(BaseModel):
    fx_rate: float = 15.42
    total_mvr: float
    fx_timestamp: str

class QuoteApproval(BaseModel):
    fce_verified: bool
    human_can_send: bool
    manager_approval_required: bool
    discount_allowed: bool

class Compliance(BaseModel):
    tgst_rate_used: float = 0.17
    green_tax_rule_checked: bool = True
    service_charge_rule_checked: bool = True
    pricing_method: str = "Base + Margin + SC + TGST + Green Tax + Transfer"
    warnings: List[str] = []

class ShadowMetadata(BaseModel):
    event: str
    audit_hash: str
    parent_hash: str

class QuoteResponse(BaseModel):
    request_id: str
    lead_id: str
    quote_id: str
    status: QuoteStatus
    quote_valid_until: str
    currency: str = "USD"
    quote_summary: Dict
    price_breakdown: PriceBreakdown
    mvr_equivalent: MVREquivalent
    approval: QuoteApproval
    compliance: Compliance
    shadow: ShadowMetadata

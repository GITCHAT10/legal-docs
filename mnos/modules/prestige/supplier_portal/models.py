from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date

class ExtractedRoomRate(BaseModel):
    category_code: str
    category_name: str
    season_name: str
    start_date: str
    end_date: str
    sgl_rate: float
    dbl_rate: float
    trpl_rate: float
    quad_rate: float
    extra_adult_rate: float
    child_rate: float

class ExtractedMealPlanRule(BaseModel):
    plan_code: str # BB, HB, FB, AI
    adult_supplement: float
    child_supplement: float

class ExtractedTransferRule(BaseModel):
    transfer_type: str # SEAPLANE, SPEEDBOAT, DOMESTIC
    adult_rate: float
    child_rate: float
    baggage_allowance_kg: float
    excess_baggage_rate: float

class ExtractedCancellationRule(BaseModel):
    deadline_days: int
    penalty_percent: float

class ContractExtractionResult(BaseModel):
    resort_name: str
    star_rating: Optional[float] = None
    effective_period: Dict[str, str]
    room_rates: List[ExtractedRoomRate] = []
    meal_plans: List[ExtractedMealPlanRule] = []
    transfers: List[ExtractedTransferRule] = []
    cancellation_policies: List[ExtractedCancellationRule] = []
    minimum_stay: int = 1
    compulsory_festive_supplements: Dict[str, float] = {}
    special_offers: List[Dict] = []
    status: str = "DRAFT"

class FinanceReviewRecord(BaseModel):
    approved: bool
    tax_treatment_confirmed: bool
    payment_terms_confirmed: bool
    comments: Optional[str] = None
    reviewer_id: str
    reviewed_at: str

class RevenueReviewRecord(BaseModel):
    approved: bool
    markup_floor_confirmed: bool
    yield_strategy_confirmed: bool
    comments: Optional[str] = None
    reviewer_id: str
    reviewed_at: str

class CMOMarketStrategyProfile(BaseModel):
    EU_markup_percent: float = 15.0
    CIS_markup_percent: float = 20.0
    GCC_markup_percent: float = 20.0
    Asia_markup_percent: float = 15.0
    India_markup_percent: float = 12.0
    China_markup_percent: float = 15.0
    Global_UHNW_markup_percent: float = 25.0
    agent_commission_percent: float = 10.0
    VIP_Black_Book_premium_percent: float = 5.0
    market_visibility: List[str] = ["GLOBAL"]

class MarketSellingRate(BaseModel):
    market_region: str
    category_code: str
    selling_rate: float
    tax_breakdown: Dict[str, float]
    margin_amount: float
    commission_amount: float
    safe_to_publish: bool = False

class SpecialOffer(BaseModel):
    offer_id: str
    offer_name: str
    offer_type: str
    room_categories: List[str]
    travel_dates: Dict[str, str]
    discount_value: float
    status: str = "PENDING_APPROVAL"

class SupplierAction(BaseModel):
    action_id: str
    supplier_id: str
    resort_id: str
    action_type: str
    submitted_by_actor_id: str
    submitted_at: str
    payload: Dict[str, Any]
    status: str = "SUPPLIER_SUBMITTED"
    trace_id: str
    shadow_refs: List[str] = []

class AdminApprovalTask(BaseModel):
    task_id: str
    action_id: str
    required_approvals: List[str]
    current_stage: str
    approval_history: List[Dict] = []

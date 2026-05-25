from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import date

class ChannelType(str, Enum):
    B2C_DIRECT = "B2C_DIRECT"
    B2B_AGENT = "B2B_AGENT"
    B2B2C_AGENT_TO_GUEST = "B2B2C_AGENT_TO_GUEST"
    B2G_GOVERNMENT = "B2G_GOVERNMENT"
    VIP_PRIVATE = "VIP_PRIVATE"
    BLACK_BOOK = "BLACK_BOOK"
    CORPORATE = "CORPORATE"
    OTA_PUBLIC = "OTA_PUBLIC"
    SUPPLIER_DIRECT = "SUPPLIER_DIRECT"
    INTERNAL_TEST = "INTERNAL_TEST"

class VisibilityScope(str, Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    RESTRICTED = "RESTRICTED"
    P3_PRIVACY = "P3_PRIVACY"
    P4_PRIVACY = "P4_PRIVACY"

class RateApprovalStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    AI_EXTRACTED_DRAFT = "AI_EXTRACTED_DRAFT"
    SUPPLIER_CONFIRMED = "SUPPLIER_CONFIRMED"
    FINANCE_REVIEW_REQUIRED = "FINANCE_REVIEW_REQUIRED"
    FINANCE_APPROVED = "FINANCE_APPROVED"
    REVENUE_REVIEW_REQUIRED = "REVENUE_REVIEW_REQUIRED"
    REVENUE_APPROVED = "REVENUE_APPROVED"
    CMO_MARKET_APPROVAL_REQUIRED = "CMO_MARKET_APPROVAL_REQUIRED"
    CMO_APPROVED_FOR_MARKET = "CMO_APPROVED_FOR_MARKET"
    MAC_EOS_VALIDATED = "MAC_EOS_VALIDATED"
    FCE_VALIDATED = "FCE_VALIDATED"
    SHADOW_SEALED = "SHADOW_SEALED"
    ACTIVE_FOR_SALE = "ACTIVE_FOR_SALE"
    REJECTED = "REJECTED"

class SupplierActionType(str, Enum):
    RATE_SHEET_UPLOAD = "RATE_SHEET_UPLOAD"
    CONTRACT_PDF_UPLOAD = "CONTRACT_PDF_UPLOAD"
    STOP_SELL = "STOP_SELL"
    OPEN_SALE = "OPEN_SALE"
    ADD_SPECIAL = "ADD_SPECIAL"
    EDIT_ALLOTMENT = "EDIT_ALLOTMENT"

class MarketSellingRate(BaseModel):
    rate_id: str
    supplier_id: str
    product_id: str
    channel_type: ChannelType
    visibility_scope: VisibilityScope

    base_net_rate: float
    public_rate: float
    agent_net_rate: float
    agent_commission_rate: float
    b2b_agent_net_rate: float
    b2b_agent_commission_rate: float
    b2b2c_guest_rate: float
    corporate_rate: float
    government_rate: float
    vip_private_rate: float
    black_book_rate: float
    ota_public_rate: float

    # Regional selling rates
    EU_selling_rate: float = 0.0
    CIS_selling_rate: float = 0.0
    GCC_selling_rate: float = 0.0
    Asia_selling_rate: float = 0.0
    India_selling_rate: float = 0.0
    China_selling_rate: float = 0.0
    Domestic_Maldives_selling_rate: float = 0.0

    package_rate: float
    room_only_rate: float
    room_plus_transfer_rate: float
    room_plus_experience_rate: float

    legal_tax_breakdown: Dict[str, float] = {}
    margin_breakdown: Dict[str, float] = {}
    commission_breakdown: Dict[str, float] = {}

    safe_to_publish: bool = False
    approval_status: RateApprovalStatus = RateApprovalStatus.DRAFT
    audit_seal: Optional[str] = None
    trace_id: str

    metadata: Dict[str, Any] = {}

class SupplierContract(BaseModel):
    contract_id: str
    supplier_id: str
    resort_name: str
    effective_from: date
    effective_to: date
    status: RateApprovalStatus = RateApprovalStatus.DRAFT
    extracted_data: Dict[str, Any] = {}
    audit_trail: List[Dict[str, Any]] = []

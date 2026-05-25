from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from decimal import Decimal

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
    FINANCE_APPROVED = "FINANCE_APPROVED"
    REVENUE_APPROVED = "REVENUE_APPROVED"
    CMO_APPROVED = "CMO_APPROVED"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"

class MarketSellingRate(BaseModel):
    rate_id: str
    supplier_id: str
    product_id: str
    channel_type: ChannelType
    visibility_scope: VisibilityScope

    base_net_rate: float
    public_rate: float
    b2b_agent_net_rate: float
    b2b_agent_commission_rate: float
    b2b2c_guest_rate: float
    corporate_rate: float
    government_rate: float
    vip_private_rate: float
    black_book_rate: float
    ota_public_rate: float
    package_rate: float
    room_plus_transfer_rate: float
    room_plus_experience_rate: float

    safe_to_publish: bool = False
    approval_status: RateApprovalStatus = RateApprovalStatus.DRAFT
    audit_seal: Optional[str] = None

    metadata: Dict[str, Any] = {}

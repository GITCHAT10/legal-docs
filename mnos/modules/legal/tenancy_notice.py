from typing import Dict, Any
from mnos.modules.shadow.service import shadow
from mnos.core.events.service import events

class TenancyNoticeService:
    """
    eLEGAL Tenancy Notice Flow: FCE shortfall → EVENTS → SILVIA → ABAC → draft notice → lawyer approval → SHADOW.
    """
    def generate_draft_notice(self, lease_id: str, shortfall_amount: float) -> Dict[str, Any]:
        notice = {
            "lease_id": lease_id,
            "shortfall": shortfall_amount,
            "status": "DRAFT_PENDING_LAWYER_APPROVAL",
            "type": "14_DAY_NOTICE"
        }
        shadow.commit("elegal.tenancy.notice_drafted", notice)
        return notice

    def approve_notice(self, notice_id: str, lawyer_id: str) -> Dict[str, Any]:
        approval = {
            "notice_id": notice_id,
            "lawyer_id": lawyer_id,
            "status": "APPROVED_FOR_DISPATCH",
            "delivery_mode": "MOCK_SILVIA"
        }
        shadow.commit("elegal.tenancy.notice_approved", approval)
        return approval

tenancy_notice = TenancyNoticeService()

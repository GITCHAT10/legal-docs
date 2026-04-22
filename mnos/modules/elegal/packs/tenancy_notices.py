from typing import Dict, Any, List
from datetime import datetime
from mnos.modules.shadow.service import shadow
from mnos.modules.elegal.packs.tenancy import tenancy_engine

class TenancyNotices:
    """
    Tenancy Dispute and Notice Engine: Formalizing enforcement.
    Automates legal demand generation and dispute classification.
    """
    def issue_late_rent_notice(self, lease_id: str, days_late: int) -> Dict[str, Any]:
        lease = tenancy_engine.get_lease(lease_id)
        notice = {
            "lease_id": lease_id,
            "anchor_id": lease["anchor_id"],
            "type": "LATE_RENT_DEMAND",
            "days_late": days_late,
            "legal_status": "FORMAL_NOTICE_ISSUED",
            "timestamp": datetime.now().isoformat()
        }
        shadow.commit("elegal.tenancy.notice_issued", notice)
        return notice

    def trigger_dispute(self, lease_id: str, category: str, details: str) -> Dict[str, Any]:
        """
        Classifies disputes (DEPOSIT, EVICTION, MAINTENANCE) for eLEGAL Pulse.
        """
        lease = tenancy_engine.get_lease(lease_id)
        dispute = {
            "lease_id": lease_id,
            "anchor_id": lease["anchor_id"],
            "category": category, # DEPOSIT, EVICTION, etc.
            "details": details,
            "status": "OPEN",
            "timestamp": datetime.now().isoformat()
        }
        shadow.commit("elegal.tenancy.dispute_triggered", dispute)
        return dispute

tenancy_notices = TenancyNotices()

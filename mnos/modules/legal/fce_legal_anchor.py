from decimal import Decimal
from typing import Dict, Any, Optional
from mnos.modules.shadow.service import shadow

class FceLegalAnchor:
    """
    eLEGAL Extended Anchor: Advanced financial-legal binding for v0.3.
    """
    def __init__(self, matter_id: str, anchor_id: str, brand: str, tin: str):
        self.matter_id = matter_id
        self.anchor_id = anchor_id
        self.brand = brand
        self.tin = tin
        self.amount_due = Decimal("0.00")
        self.amount_paid = Decimal("0.00")

    def sync_fce(self, amount: Decimal) -> Dict[str, Any]:
        self.amount_paid += amount
        balance = self.amount_due - self.amount_paid

        status = {
            "matter_id": self.matter_id,
            "anchor_id": self.anchor_id,
            "brand": self.brand,
            "tin": self.tin,
            "outstanding_balance": str(balance),
            "reconciliation_status": "BALANCED" if balance <= 0 else "SHORTFALL_DETECTED",
            "shadow_hash": "H-PENDING"
        }

        shadow.commit("elegal.fce.anchor_synced", status)
        return status

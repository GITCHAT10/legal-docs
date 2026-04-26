from enum import Enum
from typing import Dict, Any, Optional
from decimal import Decimal
from mnos.modules.finance.dashboard.service import dashboard_service
from mnos.modules.shadow.service import shadow

class GateStatus(Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"

class SmartContractGate:
    """
    BUBBLE Smart Contract Execution Gate.
    Enforces preflight validation for all automated payouts.
    """
    def __init__(self, approval_threshold: Decimal = Decimal("10000.00")):
        self.approval_threshold = approval_threshold

    def run_preflight(self, vendor_id: str, amount: Decimal) -> Dict[str, Any]:
        """
        Executes multi-factor preflight checks.
        1. Liquidity Check
        2. P&L Health Check
        3. Ledger Integrity Check
        4. Approval Threshold Check
        """
        metrics = dashboard_service.get_mtd_pnl()
        cash = dashboard_service.get_cash_position()

        # 1. Ledger Integrity Check (Fail-Closed)
        if not shadow.verify_integrity():
            return {"status": GateStatus.DENY, "reason": "LEDGER_INTEGRITY_FAILURE"}

        # 2. Liquidity Check (Cash > Payout + Tax Escrow)
        total_payout_with_tax = amount * Decimal("1.27") # SC + TGST approximation
        if cash["liquid_cash"] < (total_payout_with_tax + cash["tgst_escrow"]):
            return {"status": GateStatus.DENY, "reason": "INSUFFICIENT_LIQUIDITY"}

        # 3. P&L Health Check (MTD Net > 0)
        if metrics["net_profit"] < 0:
            return {"status": GateStatus.DENY, "reason": "NEGATIVE_PNL_BLOCK"}

        # 4. Soft Gate (COFGO Approval Threshold)
        if amount > self.approval_threshold:
            return {"status": GateStatus.REQUIRES_APPROVAL, "reason": "COFGO_THRESHOLD_EXCEEDED"}

        return {"status": GateStatus.ALLOW, "reason": "PREFLIGHT_PASSED"}

gate = SmartContractGate()

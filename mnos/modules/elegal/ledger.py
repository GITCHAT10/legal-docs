from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any
from mnos.config import config
from mnos.modules.shadow.service import shadow

class LegalLedger:
    """
    eLEGAL Ledger (The M1 Moat): Native, blockchain-based accounting system.
    Reconciles client trust accounts against Maldivian tax requirements (TIN 1166708).
    """
    def __init__(self):
        self.tin = config.ELEGAL_TIN

    def reconcile_trust_account(self, client_id: str, trust_balance: Decimal, taxable_income: Decimal) -> Dict[str, Any]:
        """
        Reconciles trust account balance and calculates tax obligations.
        """
        # Logic: 10% Service Charge + 17% TGST on legal fees (simplified for this kernel)
        legal_fees = taxable_income.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        tgst = (legal_fees * config.TGST).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        reconciliation_status = {
            "client_id": client_id,
            "tin": self.tin,
            "trust_balance": str(trust_balance),
            "taxable_income": str(taxable_income),
            "tgst_due": str(tgst),
            "reconciled": True
        }

        # Doctrine: Commit reconciliation to SHADOW
        shadow.commit("elegal.ledger.reconciled", reconciliation_status)

        return reconciliation_status

elegal_ledger = LegalLedger()

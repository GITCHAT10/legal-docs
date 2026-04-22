from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List
from mnos.modules.elegal.ledger import elegal_ledger
from mnos.modules.shadow.service import shadow

class LegalFinance:
    """
    eLEGAL Legal Billing and Financial Analytics.
    Manages fee structures, expense tracking, and profit/loss analytics.
    Integrated with eLEGAL Ledger for tax compliance.
    """
    def __init__(self):
        self.billings: List[Dict[str, Any]] = []

    def generate_invoice(self, client_id: str, amount: Decimal, description: str) -> Dict[str, Any]:
        """
        Generates a legal invoice and reconciles via eLEGAL Ledger.
        """
        # 1. Reconcile tax via Ledger (M1 Moat)
        reconciliation = elegal_ledger.reconcile_trust_account(
            client_id=client_id,
            trust_balance=Decimal("0.00"), # Mocked balance
            taxable_income=amount
        )

        invoice = {
            "invoice_id": f"INV-L-{len(self.billings) + 1000}",
            "client_id": client_id,
            "amount": str(amount),
            "description": description,
            "tax_details": reconciliation,
            "status": "ISSUED"
        }

        self.billings.append(invoice)
        shadow.commit("elegal.billing.processed", invoice)
        return invoice

    def get_financial_summary(self) -> Dict[str, Any]:
        """
        Calculates profit/loss and total tax due.
        """
        total_revenue = sum(Decimal(b["amount"]) for b in self.billings)
        total_tgst = sum(Decimal(b["tax_details"]["tgst_due"]) for b in self.billings)

        return {
            "total_revenue": str(total_revenue),
            "total_tgst_due": str(total_tgst),
            "net_revenue": str(total_revenue - total_tgst)
        }

legal_finance = LegalFinance()

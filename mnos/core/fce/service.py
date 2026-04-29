from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any

class FCESovereignService:
    """
    FCE Sovereignty Service for SALA Node.
    Enforces MIRA-compliant Maldives Billing Rules.
    Implements Invoice Idempotency.
    """
    def __init__(self, mira_mode: bool = True):
        self.mira_mode = mira_mode
        self.generated_invoices = {} # idempotency_key -> invoice

    def calculate_order(self, base_price: float, category: str = None, idempotency_key: str = None) -> Dict[str, Any]:
        """
        Calculates order with MIRA rules.
        Locks result to idempotency_key to prevent double invoice generation.
        """
        if base_price is None or base_price <= 0:
             raise ValueError("ExecutionValidationError: Amount must be greater than zero")

        if category is None:
             raise ValueError("ExecutionValidationError: Tax context required")

        if idempotency_key and idempotency_key in self.generated_invoices:
            return self.generated_invoices[idempotency_key]

        base = Decimal(str(base_price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 1. 10% Service Charge
        sc = (base * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal = base + sc

        # 2. TGST (17%) or GST (8%)
        tax_rate = Decimal("0.17") if category in ["TOURISM", "RESORT_SUPPLY"] else Decimal("0.08")
        tax_amt = (subtotal * tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total = subtotal + tax_amt

        invoice = {
            "base": float(base),
            "service_charge": float(sc),
            "subtotal": float(subtotal),
            "tax_rate": float(tax_rate),
            "tax_amount": float(tax_amt),
            "total": float(total),
            "currency": "MVR",
            "idempotency_key": idempotency_key
        }

        if idempotency_key:
            self.generated_invoices[idempotency_key] = invoice

        return invoice

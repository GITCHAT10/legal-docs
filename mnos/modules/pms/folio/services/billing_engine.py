from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, UTC
from typing import Dict, Any

class BillingEngine:
    """
    FCE PMS Layer: Maldives-Compliant Billing Engine.
    Handles SC, TGST, and USD-denominated Green Tax.
    """
    def __init__(self, locked_fx_rate: Decimal = Decimal("15.42")):
        self.locked_fx_rate = locked_fx_rate # MVR per 1 USD

    def calculate_charge(
        self,
        base_amount: Decimal,
        category: str = "ROOM",
        green_tax_pax: int = 0,
        green_tax_nights: int = 0
    ) -> Dict[str, Any]:
        """
        Calculates subtotal, SC, TGST, and Green Tax.
        Parity-safe: Bundles/Charges calculated in MVR with FX locking.
        """
        # 1. 10% Service Charge
        sc_rate = Decimal("0.10")
        sc_amt = (base_amount * sc_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal = base_amount + sc_amt

        # 2. TGST (17% for tourism-linked)
        tax_rate = Decimal("0.17") if category in ["ROOM", "TOURISM"] else Decimal("0.08")
        tax_amt = (subtotal * tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 3. Green Tax (USD fixed, converted to MVR)
        gt_rate_usd = Decimal("6.00")
        gt_amt_usd = (Decimal(str(green_tax_pax)) * Decimal(str(green_tax_nights)) * gt_rate_usd)
        gt_amt_mvr = (gt_amt_usd * self.locked_fx_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total = subtotal + tax_amt + gt_amt_mvr

        return {
            "base": float(base_amount),
            "service_charge": float(sc_amt),
            "subtotal": float(subtotal),
            "tax_amount": float(tax_amt),
            "green_tax_mvr": float(gt_amt_mvr),
            "total": float(total),
            "fx_rate": float(self.locked_fx_rate)
        }

    def get_signed_fx_rate(self) -> Dict[str, Any]:
        """Simulates MVB Central Bank API signed rate."""
        return {
            "rate": float(self.locked_fx_rate),
            "source": "MVB_CENTRAL_BANK",
            "locked_at": datetime.now(UTC).isoformat(),
            "signature": "SIG-FX-HARDENED-PROOF"
        }

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any

class FCESovereignService:
    """
    FCE Sovereignty Service for SALA Node.
    Enforces MIRA-compliant Maldives Billing Rules.
    """
    def __init__(self, mira_mode: bool = True):
        self.mira_mode = mira_mode

    def calculate_order(self, base_price: float, category: str = "RETAIL") -> Dict[str, Any]:
        base = Decimal(str(base_price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 1. 10% Service Charge
        sc = (base * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal = base + sc

        # 2. TGST (17%) or GST (8%)
        tax_rate = Decimal("0.17") if category in ["TOURISM", "RESORT_SUPPLY"] else Decimal("0.08")
        tax_amt = (subtotal * tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total = subtotal + tax_amt

        return {
            "base": float(base),
            "service_charge": float(sc),
            "subtotal": float(subtotal),
            "tax_rate": float(tax_rate),
            "tax_amount": float(tax_amt),
            "total": float(total),
            "currency": "MVR"
        }

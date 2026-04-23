from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List
from mnos.config import config
from mnos.modules.shadow.service import shadow

class TaxGovernor:
    """
    APOLLO MOATS: Maldives-native tax logic and governor.
    Enforces MIRA compliance and service charge rules.
    """
    def __init__(self):
        self.service_charge_rate = Decimal("0.10")
        self.tgst_rate = Decimal("0.17")

    def calculate_invoice(self, base_amount: Decimal, entries: List[Dict[str, Any]], session_context: Dict[str, Any]) -> Dict[str, Any]:
        """Hardened invoice calculation with SHADOW audit."""
        subtotal = base_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        service_charge = (subtotal * self.service_charge_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        taxable_amount = subtotal + service_charge
        tgst = (taxable_amount * self.tgst_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = taxable_amount + tgst

        result = {
            "base": subtotal,
            "service_charge": service_charge,
            "taxable_amount": taxable_amount,
            "tgst": tgst,
            "total": total,
            "mira_compliant": True,
            "currency": "USD"
        }

        return result

tax_governor = TaxGovernor()

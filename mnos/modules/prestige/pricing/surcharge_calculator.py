from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any

class SurchargeCalculator:
    def apply_taxes(self, base_surcharge: Decimal, tax_inclusive: bool = False) -> Dict[str, Any]:
        """
        Applies 10% Service Charge + 17% TGST on festive surcharges.
        """
        if tax_inclusive:
            return {
                "base": float(base_surcharge),
                "service_charge": 0.0,
                "tgst": 0.0,
                "total": float(base_surcharge)
            }

        sc = (base_surcharge * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal = base_surcharge + sc
        tgst = (subtotal * Decimal("0.17")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = subtotal + tgst

        return {
            "base": float(base_surcharge),
            "service_charge": float(sc),
            "tgst": float(tgst),
            "total": float(total)
        }

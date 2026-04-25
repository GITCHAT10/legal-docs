from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any

class RegionalTaxEngine:
    """
    Regional Tax Injectors:
    Implements statutory tax logic for different jurisdictions.
    """
    def calculate_tax(self, amount: Decimal, region: str) -> Dict[str, Any]:
        if region == 'MV':
            return self._mv_mira(amount)
        elif region == 'TH':
            return self._th_rd(amount)
        elif region == 'VN':
            return self._vn_tax(amount)
        elif region == 'IN':
            return self._in_gst(amount)
        else:
            return {"tax": Decimal('0.00'), "engine": "GENERIC"}

    def _mv_mira(self, amount: Decimal) -> Dict[str, Any]:
        # TGST 17%
        tgst = (amount * Decimal('0.17')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return {"tax": tgst, "engine": "MV_MIRA", "currency": "MVR"}

    def _th_rd(self, amount: Decimal) -> Dict[str, Any]:
        # VAT 7%
        vat = (amount * Decimal('0.07')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return {"tax": vat, "engine": "TH_RD", "currency": "THB"}

    def _vn_tax(self, amount: Decimal) -> Dict[str, Any]:
        # VAT 10%
        vat = (amount * Decimal('0.10')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return {"tax": vat, "engine": "VN_TAX", "currency": "VND"}

    def _in_gst(self, amount: Decimal) -> Dict[str, Any]:
        # GST 18%
        gst = (amount * Decimal('0.18')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return {"tax": gst, "engine": "IN_GST", "currency": "INR"}

tax_engine = RegionalTaxEngine()

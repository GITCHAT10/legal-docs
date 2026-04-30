from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any

class PrestigePricingEngine:
    def __init__(self, fx_rate: Decimal = Decimal("15.42")):
        self.fx_rate = fx_rate # MVR per USD

    def calculate_luxury_package(self, base_price_usd: Decimal, nights: int, adults: int) -> Dict[str, Any]:
        """
        PRESTIGE MALDIVES TAX DOCTRINE:
        Subtotal = Base + 10% Service Charge
        TGST = 17% on Subtotal
        Green Tax = $12 USD per person per night (for luxury resorts)
        """
        base_mvr = (base_price_usd * self.fx_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 1. 10% Service Charge
        service_charge = (base_mvr * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal = base_mvr + service_charge

        # 2. 17% TGST on Subtotal
        tgst_rate = Decimal("0.17")
        tgst_amount = (subtotal * tgst_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 3. Green Tax ($12 USD per person/night)
        green_tax_rate_usd = Decimal("12.00")
        green_tax_usd = green_tax_rate_usd * adults * nights
        green_tax_mvr = (green_tax_usd * self.fx_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        final_price_mvr = subtotal + tgst_amount + green_tax_mvr

        return {
            "net_base_usd": float(base_price_usd),
            "net_base_mvr": float(base_mvr),
            "service_charge_mvr": float(service_charge),
            "subtotal_mvr": float(subtotal),
            "tgst_rate": float(tgst_rate),
            "tgst_amount_mvr": float(tgst_amount),
            "green_tax_usd": float(green_tax_usd),
            "green_tax_mvr": float(green_tax_mvr),
            "total_mvr": float(final_price_mvr),
            "fx_rate_applied": float(self.fx_rate),
            "currency": "MVR"
        }

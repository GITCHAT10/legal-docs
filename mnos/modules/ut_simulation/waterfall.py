from typing import Dict, Any
import logging
from decimal import Decimal

class QTRevenueWaterfall:
    """
    QT Revenue Waterfall Simulation.
    GROSS → TAX(17% TGST) → PLATFORM_FEE → LEASE → FUEL → NET
    """
    def calculate_waterfall(self, gross: Decimal) -> Dict[str, Decimal]:
        tax = (gross * Decimal("0.17")).quantize(Decimal("0.01"))
        platform = (gross * Decimal("0.05")).quantize(Decimal("0.01"))
        lease = Decimal("5000.00") # Fixed lease sim
        fuel = (gross * Decimal("0.15")).quantize(Decimal("0.01"))
        net = gross - tax - platform - lease - fuel

        return {
            "gross": gross,
            "tax": tax,
            "platform_fee": platform,
            "lease": lease,
            "fuel": fuel,
            "net": net
        }

waterfall_sim = QTRevenueWaterfall()

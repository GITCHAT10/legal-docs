from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, UTC
import hashlib
import json
from typing import Dict, Optional

class BlackCoralPricing:
    """Sovereign pricing logic for UHA Black Coral Standard"""

    BASE_VALUES_USD = {
        "BCA": Decimal("45.00"),   # Associate
        "BCO": Decimal("95.00"),   # Operator
        "BCC": Decimal("195.00"),  # Curator
        "BCD": Decimal("450.00"),  # Director
        "BCM": Decimal("2500.00")  # Master
    }

    SOVEREIGNTY_PREMIUM_MVR = Decimal("75.00")
    PDPA_PLUS_FEE_MVR = Decimal("30.00")

    VOLUME_THRESHOLDS = [
        (10, Decimal("0.95")),   # 5% off
        (25, Decimal("0.90")),   # 10% off
        (50, Decimal("0.85")),   # 15% off
    ]

    def __init__(self, core):
        self.core = core

    def calculate_price(self, tier: str, quantity: int = 1, resort_id: str = None) -> Dict:
        base_usd = self.BASE_VALUES_USD.get(tier, Decimal("45.00"))

        discount = Decimal("1.00")
        for threshold, rate in self.VOLUME_THRESHOLDS:
            if quantity >= threshold:
                discount = rate

        discounted_usd = base_usd * discount

        # Fixed rate for demo
        fx_rate = Decimal("15.42")

        unit_mvr = (
            (discounted_usd * fx_rate) +
            self.SOVEREIGNTY_PREMIUM_MVR +
            self.PDPA_PLUS_FEE_MVR
        ).quantize(Decimal("5.00"), rounding=ROUND_HALF_UP)

        total_mvr = unit_mvr * quantity
        total_usd = (total_mvr / fx_rate).quantize(Decimal("0.01"))

        return {
            "tier": tier,
            "quantity": quantity,
            "unit_price_mvr": float(unit_mvr),
            "total_price_mvr": float(total_mvr),
            "total_price_usd": float(total_usd),
            "breakdown": {
                "base_usd": float(base_usd),
                "discount": float(discount),
                "sovereignty_premium_mvr": float(self.SOVEREIGNTY_PREMIUM_MVR)
            }
        }

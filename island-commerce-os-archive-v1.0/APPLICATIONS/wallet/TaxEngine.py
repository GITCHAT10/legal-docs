from decimal import Decimal, ROUND_HALF_UP

class BiologicalROIEngine:
    """
    Biological ROI Pricing Engine (SKY-i OS v1.4):
    Implements outcome-based pricing models including Recovered Hour Fees
    and Longevity Dividends.
    """
    def __init__(self):
        # 17% TGST and 10% Service Charge are handled by FCE core logic
        pass

    def calculate_recovered_hour_fee(self, hours_recovered: float, hourly_rate: Decimal) -> Decimal:
        """
        Calculates fee based on 'Recovered Hours' (biological optimization).
        Formula: Recovered Hours * Hourly Rate
        """
        if hours_recovered <= 0:
            return Decimal("0.00")

        fee = Decimal(str(hours_recovered)) * hourly_rate
        return fee.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_longevity_dividend(self, healthspan_gain_days: float, base_dividend: Decimal) -> Decimal:
        """
        Calculates 'Longevity Dividend' based on projected healthspan increase.
        Formula: Healthspan Gain (Days) * Base Dividend per Day
        """
        if healthspan_gain_days <= 0:
            return Decimal("0.00")

        dividend = Decimal(str(healthspan_gain_days)) * base_dividend
        return dividend.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_esg_regen_premium(self, regen_score: float, base_price: Decimal) -> Decimal:
        """
        Calculates a 'Regen Premium' for Eco-Sovereign guests stay.
        Weighted by Regen Score.
        """
        if regen_score < 80:
             return Decimal("0.00") # No premium for standard stays

        # Premium ranges from 5% to 15% depending on regen score (80-100)
        premium_rate = Decimal(str((regen_score - 80) / 20 * 0.10 + 0.05))
        premium = base_price * premium_rate
        return premium.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

pricing_engine = BiologicalROIEngine()

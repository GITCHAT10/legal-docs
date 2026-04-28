import structlog
from decimal import Decimal, ROUND_HALF_UP

logger = structlog.get_logger("finance.fx_compliance")

class FXComplianceEngine:
    """
    Maldives FX Compliance Engine: Enforces MMA ±2% rate rules
    and mandatory 20% USD-to-MVR conversion.
    """
    def __init__(self):
        # Default MMA peg for MVR/USD
        self.MMA_RATE = Decimal("15.42")
        self.monthly_usd_revenue = Decimal("0")
        self.converted_to_mvr = Decimal("0")

    def get_compliant_fx_rate(self, current_mma_rate: Decimal = None) -> Decimal:
        """
        Calculates a legal FX rate within the ±2% MMA buffer.
        Strategy: Add 1% buffer for margin but cap at legal limits.
        """
        base_rate = current_mma_rate or self.MMA_RATE
        target = (base_rate * Decimal("1.01")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        lower_bound = base_rate * Decimal("0.98")
        upper_bound = base_rate * Decimal("1.02")

        if target < lower_bound:
            return lower_bound.quantize(Decimal("0.02"), rounding=ROUND_HALF_UP)
        elif target > upper_bound:
            return upper_bound.quantize(Decimal("0.02"), rounding=ROUND_HALF_UP)

        return target

    def calculate_mandatory_conversion(self, total_usd: Decimal) -> Decimal:
        """Rule: 20% of USD revenue must be converted to MVR."""
        return (total_usd * Decimal("0.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def track_revenue(self, usd_amount: Decimal):
        """Internal tracker for monthly conversion monitoring."""
        self.monthly_usd_revenue += usd_amount
        required = self.calculate_mandatory_conversion(self.monthly_usd_revenue)

        logger.info("fx_conversion_tracking",
                    total_usd=float(self.monthly_usd_revenue),
                    required_mvr_conversion=float(required),
                    remaining=float(required - self.converted_to_mvr))

    def record_conversion(self, mvr_amount: Decimal):
        """Records a bank transfer from USD to MVR."""
        self.converted_to_mvr += mvr_amount
        logger.info("mvr_conversion_recorded",
                    amount=float(mvr_amount),
                    total_converted=float(self.converted_to_mvr))

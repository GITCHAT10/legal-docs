from decimal import Decimal, ROUND_HALF_EVEN

def round_bankers(amount: float) -> float:
    """Banker's Rounding: Round to nearest even."""
    return float(Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN))

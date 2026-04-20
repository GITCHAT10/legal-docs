from typing import Dict
from decimal import Decimal, ROUND_HALF_UP

# MIRA compliant rates (using Decimal for precision)
SERVICE_CHARGE_RATE = Decimal("0.10")
TGST_RATE = Decimal("0.17")
GREEN_TAX_USD = Decimal("6.00")

def calculate_maldives_taxes(base_amount: float | Decimal, apply_green_tax: bool = False, nights: int = 0) -> Dict:
    """
    Hardened MIRA tax calculation using Decimal and ROUND_HALF_UP.
    """
    if not isinstance(base_amount, Decimal):
        base_amount = Decimal(str(base_amount))

    sc = (base_amount * SERVICE_CHARGE_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # TGST is 17% on (Base + Service Charge)
    tgst = ((base_amount + sc) * TGST_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    green_tax = (GREEN_TAX_USD * nights).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if apply_green_tax else Decimal("0.00")

    total = base_amount + sc + tgst + green_tax

    return {
        "base_amount": base_amount,
        "service_charge": sc,
        "tgst": tgst,
        "green_tax": green_tax,
        "total_amount": total
    }

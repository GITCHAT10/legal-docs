from datetime import date
from typing import Dict, Any
from mnos.shared.finance.rounding import round_bankers

def calculate_maldives_taxes(base_amount: float, business_date: date, apply_green_tax: bool = False, nights: int = 0) -> Dict[str, float]:
    """
    Centralized Sovereign Tax Logic for FCE.
    MIRA/LRA compliant: 10% Service Charge + 17% TGST on subtotal.
    """
    # 1. 10% Service Charge
    service_charge = round_bankers(base_amount * 0.10)

    # 2. Subtotal = Base + SC
    subtotal = base_amount + service_charge

    # 3. 17% TGST
    tgst_rate = 0.17
    tgst = round_bankers(subtotal * tgst_rate)

    # 4. Green Tax ( per pax per night)
    green_tax = round_bankers(6.0 * nights) if apply_green_tax else 0.0

    total_amount = round_bankers(subtotal + tgst + green_tax)

    return {
        "base_amount": base_amount,
        "service_charge": service_charge,
        "tgst": tgst,
        "green_tax": green_tax,
        "total_amount": total_amount,
        "tgst_rate": tgst_rate
    }

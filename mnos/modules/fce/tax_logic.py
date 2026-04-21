from datetime import date
from typing import Dict, Any

def calculate_maldives_taxes(base_amount: float, business_date: date, apply_green_tax: bool = False, nights: int = 0) -> Dict[str, float]:
    """
    Centralized Sovereign Tax Logic for FCE.
    MIRA/LRA compliant: 10% Service Charge + 17% TGST on subtotal.
    """
    # 1. 10% Service Charge
    service_charge = base_amount * 0.10

    # 2. Subtotal = Base + SC
    subtotal = base_amount + service_charge

    # 3. 17% TGST (Effective July 1, 2025)
    tgst_rate = 0.17 if business_date >= date(2025, 7, 1) else 0.16
    tgst = subtotal * tgst_rate

    # 4. Green Tax (Effective Jan 1, 2025: $12 per day for resorts)
    daily_green_tax_rate = 12.0 if business_date >= date(2025, 1, 1) else 6.0
    green_tax = daily_green_tax_rate * nights if apply_green_tax else 0.0

    total_amount = round(subtotal + tgst + green_tax, 2)

    return {
        "base_amount": base_amount,
        "service_charge": service_charge,
        "tgst": tgst,
        "green_tax": green_tax,
        "total_amount": total_amount,
        "tgst_rate": tgst_rate,
        "green_tax_rate": daily_green_tax_rate
    }

from typing import Dict

# MIRA compliant rates
SERVICE_CHARGE_RATE = 0.10
TGST_RATE = 0.17
GREEN_TAX_USD = 6.0

def calculate_maldives_taxes(base_amount: float, apply_green_tax: bool = False, nights: int = 0) -> Dict:
    service_charge = base_amount * SERVICE_CHARGE_RATE
    tgst = (base_amount + service_charge) * TGST_RATE
    green_tax = GREEN_TAX_USD * nights if apply_green_tax else 0.0
    return {
        "base_amount": base_amount,
        "service_charge": service_charge,
        "tgst": tgst,
        "green_tax": green_tax,
        "total_amount": base_amount + service_charge + tgst + green_tax
    }

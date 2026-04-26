from datetime import date
from typing import Dict, Any
from mnos.shared.finance.rounding import round_bankers

def calculate_maldives_taxes(base_amount: float, business_date: date, apply_green_tax: bool = False, nights: int = 0, is_tourism: bool = True) -> Dict[str, float]:
    """
    Fixed Sovereign Tax Logic (MIRA Compliant):

    Tourism (Transport, Hotels, Excursions):
    → 10% Service Charge
    → 17% TGST on (Base + SC)

    Local/Non-Tourism:
    → 8% GST on Base (No SC)

    ❗ NEVER apply both to the same line item.
    """
    if is_tourism:
        service_charge = round_bankers(base_amount * 0.10)
        subtotal = base_amount + service_charge
        tgst = round_bankers(subtotal * 0.17)
        green_tax = round_bankers(6.0 * nights) if apply_green_tax else 0.0
        total_amount = round_bankers(subtotal + tgst + green_tax)

        return {
            "base_amount": base_amount,
            "service_charge": service_charge,
            "tgst": tgst,
            "green_tax": green_tax,
            "total_amount": total_amount,
            "tax_type": "TGST"
        }
    else:
        gst = round_bankers(base_amount * 0.08)
        total_amount = round_bankers(base_amount + gst)

        return {
            "base_amount": base_amount,
            "service_charge": 0.0,
            "tgst": 0.0,
            "gst": gst,
            "green_tax": 0.0,
            "total_amount": total_amount,
            "tax_type": "GST"
        }

from decimal import Decimal

def calculate_sovereign_tax(subtotal: Decimal, guest_type: str) -> dict:
    """
    Maldives Sovereign Tax Structure (April 2026):
    - Tourist: 10% Service Charge + 17% TGST on (Subtotal + SC)
    - Local:   8% GST on Subtotal
    """
    if guest_type.upper() == "TOURIST":
        service_charge = subtotal * Decimal("0.10")
        taxable_amount = subtotal + service_charge
        tgst = taxable_amount * Decimal("0.17")
        return {
            "service_charge": service_charge,
            "tax": tgst,
            "total": subtotal + service_charge + tgst,
            "schema": "TOURIST_10SC_17TGST"
        }
    else:  # LOCAL / RESIDENT
        service_charge = Decimal("0.00")
        gst = subtotal * Decimal("0.08")
        return {
            "service_charge": service_charge,
            "tax": gst,
            "total": subtotal + gst,
            "schema": "LOCAL_8GST"
        }

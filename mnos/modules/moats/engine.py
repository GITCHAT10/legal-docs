from decimal import Decimal

class MoatsEngine:
    """
    MOATS v2.0 Fiscal Engine
    Enforces MIRA-compliant fiscal logic for the Maldives.
    """
    def __init__(self):
        self.service_charge_rate = Decimal("0.10")  # 10%
        self.tgst_rate = Decimal("0.17")          # 17%
        self.green_tax_rate = Decimal("6.00")     # $6 per pax/night

    def calculate_bill(self, base_amount: Decimal, pax_count: int, nights: int):
        # 10% Service Charge
        service_charge = base_amount * self.service_charge_rate

        # Subtotal (Base + SC)
        subtotal = base_amount + service_charge

        # 17% TGST applied to the subtotal
        tgst = subtotal * self.tgst_rate

        # Green Tax ($6/pax/night)
        green_tax = Decimal(str(pax_count)) * Decimal(str(nights)) * self.green_tax_rate

        total = subtotal + tgst + green_tax

        return {
            "base_amount": float(base_amount),
            "service_charge": float(service_charge),
            "subtotal": float(subtotal),
            "tgst": float(tgst),
            "green_tax": float(green_tax),
            "total": float(total)
        }

moats = MoatsEngine()

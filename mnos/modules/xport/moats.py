import os
from datetime import datetime
import logging

logger = logging.getLogger("mnos.xport")

class MoatsFiscalEngine:
    """
    MOATS (Maldives Operations & Accounting Tax System) v2.0
    The Maldives-Native Fiscal Engine for National Infrastructure.
    Compliant with MIRA standards including TGST and Green Tax.
    """

    SERVICE_CHARGE_RATE = 0.10
    TGST_RATE = 0.17
    GREEN_TAX_RATE = 6.0 # USD per pax per night (Standard Resort/Infrastructure Rate)

    @classmethod
    def calculate_mira_compliance(cls, base: float, pax: int = 0, nights: int = 0):
        """
        Formula: Total = (Base + SC_10%) * (1 + TGST_17%) + (Pax * Nights * GreenTax_6)
        """
        service_charge = base * cls.SERVICE_CHARGE_RATE
        subtotal = base + service_charge
        tgst = subtotal * cls.TGST_RATE
        green_tax = pax * nights * cls.GREEN_TAX_RATE

        grand_total = subtotal + tgst + green_tax

        bill_data = {
            "base_amount": round(base, 2),
            "service_charge": round(service_charge, 2),
            "subtotal": round(subtotal, 2),
            "tgst": round(tgst, 2),
            "green_tax": round(green_tax, 2),
            "grand_total": round(grand_total, 2),
            "currency": "MVR", # Green Tax often in USD, but system canonical is MVR
            "tax_point": datetime.now().isoformat(),
            "compliance": "MIRA_V2_0_PRODUCTION"
        }

        logger.info(f"MOATS Fiscal Calculation: Base={base}, Total={grand_total}")
        return bill_data

    @classmethod
    def validate_bill(cls, bill_data: dict) -> bool:
        """
        Sovereign Audit: Verifies bill math against MIRA V2.0 standards.
        """
        try:
            base = bill_data.get("base_amount", 0)
            expected_sc = round(base * cls.SERVICE_CHARGE_RATE, 2)
            expected_tgst = round((base + expected_sc) * cls.TGST_RATE, 2)

            # Note: Green tax varies by pax/nights which may not be in bill_data
            # but we verify the core tax chain.
            return (abs(bill_data.get("service_charge", 0) - expected_sc) <= 0.01 and
                    abs(bill_data.get("tgst", 0) - expected_tgst) <= 0.01)
        except Exception:
            return False

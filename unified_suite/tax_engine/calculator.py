import os
import logging

logger = logging.getLogger("unified_suite")

class MoatsTaxCalculator:
    """
    MOATS (Maldives Operations & Accounting Tax System)
    Unified tax logic for all Maldives Port and Airport operations.
    Follows MIRA compliance: 10% Service Charge, 17% TGST.
    """

    SERVICE_CHARGE_RATE = 0.10
    TGST_RATE = 0.17  # MIRA-compliant rate (Updated)

    # Tax Liability Ledger (MIRA-ready)
    _ledger = []

    @classmethod
    def calculate_bill(cls, base_amount: float, sc_rate: float = None, tgst_rate: float = None):
        """
        Calculates the total bill including Service Charge and TGST.
        Formula:
        1. Subtotal = Base + (Base * 10%)
        2. TGST = Subtotal * 17%
        3. Total = Subtotal + TGST
        """
        sc_r = sc_rate if sc_rate is not None else cls.SERVICE_CHARGE_RATE
        tgst_r = tgst_rate if tgst_rate is not None else cls.TGST_RATE

        service_charge = base_amount * sc_r
        subtotal = base_amount + service_charge
        tgst = subtotal * tgst_r
        total = subtotal + tgst

        bill_data = {
            "base_amount": round(base_amount, 2),
            "service_charge": round(service_charge, 2),
            "subtotal": round(subtotal, 2),
            "tgst": round(tgst, 2),
            "total_amount": round(total, 2),
            "currency": "MVR",
            "compliance": "MIRA_COMPLIANT_V2",
            "mira_ledger_id": f"MIRA-{os.urandom(4).hex().upper()}"
        }

        cls._ledger.append(bill_data)
        return bill_data

    @classmethod
    def calculate_customs_duty(cls, value: float, category: str):
        """
        Stub for Customs Duty calculation (MOATS Extended).
        Different categories might have different duty rates.
        """
        # Example: General cargo 15%
        duty_rate = 0.15
        duty = value * duty_rate
        return round(duty, 2)

    @classmethod
    def get_tax_liability_ledger(cls):
        return cls._ledger

    @classmethod
    def validate_tax_compliance(cls, bill_data: dict) -> bool:
        """
        Sovereign Validation: Ensures the bill data adheres to MIRA standards.
        - Must include Service Charge (10% of base)
        - Must include TGST (17% of subtotal)
        - Total must match summation
        """
        try:
            base = bill_data.get("base_amount", 0)
            sc = bill_data.get("service_charge", 0)
            tgst = bill_data.get("tgst", 0)
            total = bill_data.get("total_amount", 0)

            expected_sc = round(base * cls.SERVICE_CHARGE_RATE, 2)
            expected_tgst = round((base + expected_sc) * cls.TGST_RATE, 2)
            expected_total = round((base + expected_sc + expected_tgst), 2)

            # Allow for minor rounding differences (0.01)
            return (abs(sc - expected_sc) <= 0.01 and
                    abs(tgst - expected_tgst) <= 0.01 and
                    abs(total - expected_total) <= 0.01)
        except Exception:
            return False

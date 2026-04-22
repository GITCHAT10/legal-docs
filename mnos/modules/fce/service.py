from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any
from mnos.config import config

class FinancialException(Exception):
    pass

class FceService:
    """
    Financial Control Engine: Maldives-native tax logic and pre-auth.
    """
    def calculate_folio(self, base_amount: Decimal, pax: int = 1, nights: int = 1) -> Dict[str, Any]:
        """
        Strict MOATS tax logic implementation:
        1. Subtotal = Base
        2. Service Charge = 10% of Subtotal
        3. TGST = 17% of (Subtotal + Service Charge)
        4. Green Tax = $6 * pax * nights
        """
        subtotal = base_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        service_charge = (subtotal * config.SERVICE_CHARGE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        taxable_amount = subtotal + service_charge
        tgst = (taxable_amount * config.TGST).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        green_tax = (config.GREEN_TAX_USD * Decimal(pax) * Decimal(nights)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total = taxable_amount + tgst + green_tax

        return {
            "base": subtotal,
            "service_charge": service_charge,
            "taxable_amount": taxable_amount,
            "tgst": tgst,
            "green_tax": green_tax,
            "total": total,
            "currency": "USD"
        }

    def validate_pre_auth(self, folio_id: str, amount: Decimal, credit_limit: Decimal, legal_anchor_id: str = None) -> bool:
        """Mandatory validation before commit. Enforces eLEGAL binding."""
        if not legal_anchor_id:
             raise FinancialException(f"FCE AUTH DENIED: Missing Legal_Anchor_ID for folio {folio_id}. Contract linkage mandatory.")

        if amount > credit_limit:
            raise FinancialException(f"FCE AUTH DENIED: Amount {amount} exceeds limit {credit_limit} for folio {folio_id}")

        return True

fce = FceService()

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any
from mnos.config import config

class FinancialException(Exception):
    pass

class FceService:
    """
    Financial Control Engine: Maldives-native tax logic and pre-auth.
    """
    def calculate_folio(
        self,
        base_amount: Decimal,
        pax: int = 1,
        nights: int = 1,
        stay_hours: float = 24.0,
        is_child: bool = False,
        effective_tgst: Decimal = None
    ) -> Dict[str, Any]:
        """
        Hardened MIRA Compliance Logic:
        1. Subtotal = Base
        2. TGST Transition: Use effective_tgst if provided.
        3. Green Tax 12-hour rule: $0 if stay < 12h.
        4. Child Exemption: Green Tax skip if is_child=True.
        """
        tgst_rate = effective_tgst if effective_tgst is not None else config.TGST

        subtotal = base_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        service_charge = (subtotal * config.SERVICE_CHARGE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        taxable_amount = subtotal + service_charge
        tgst = (taxable_amount * tgst_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # MIRA Green Tax Rules
        green_tax = Decimal("0.00")
        if not is_child and stay_hours >= 12.0:
            green_tax = (config.GREEN_TAX_USD * Decimal(pax) * Decimal(nights)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total = taxable_amount + tgst + green_tax

        return {
            "base": subtotal,
            "service_charge": service_charge,
            "taxable_amount": taxable_amount,
            "tgst": tgst,
            "tgst_rate": tgst_rate,
            "green_tax": green_tax,
            "total": total,
            "currency": "USD",
            "mira_compliant": True
        }

    def validate_pre_auth(self, folio_id: str, amount: Decimal, credit_limit: Decimal) -> bool:
        """Mandatory validation before commit."""
        if amount > credit_limit:
            raise FinancialException(f"FCE AUTH DENIED: Amount {amount} exceeds limit {credit_limit} for folio {folio_id}")
        return True

fce = FceService()

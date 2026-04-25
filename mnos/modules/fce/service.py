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

    def validate_pre_auth(self, folio_id: str, amount: Decimal, credit_limit: Decimal) -> bool:
        """Mandatory validation before commit."""
        if amount > credit_limit:
            raise FinancialException(f"FCE AUTH DENIED: Amount {amount} exceeds limit {credit_limit} for folio {folio_id}")
        return True

    def finalize_invoice(self, folio_id: str, base_amount: Decimal, pax: int, nights: int, session_context: Dict[str, Any], connection_context: Dict[str, Any]):
        """
        Finalizes invoice with twin reporting and SHADOW logging.
        MIG HARDENING: Finalization must be explicitly audited.
        """
        from mnos.shared.guard.service import guard
        from mnos.infrastructure.mig_event_spine.service import events

        def execution_logic(payload):
            folio_data = self.calculate_folio(payload["base_amount"], payload["pax"], payload["nights"])
            # Twin Reporting: USD + MVR (Fixed rate simulation)
            mvr_rate = Decimal("15.42")
            folio_data["mvr_total"] = (folio_data["total"] * mvr_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            events.publish("sala.invoice.finalized", {
                "folio_id": payload["folio_id"],
                "data": folio_data
            })
            return folio_data

        return guard.execute_sovereign_action(
            action_type="FINALIZE_INVOICE_PROCESS",
            payload={"folio_id": folio_id, "base_amount": base_amount, "pax": pax, "nights": nights},
            session_context=session_context,
            execution_logic=execution_logic,
            connection_context=connection_context,
            tenant="MIG-GENESIS"
        )

fce = FceService()

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional
from mnos.config import config
from mnos.modules.fce.pricing_engine import pricing_engine

class FinancialException(Exception):
    pass

class FceService:
    """
    Financial Control Engine: Maldives-native tax logic and pre-auth.
    Enforces Night Audit locking and Reversal-Only Correction model.
    """
    def __init__(self):
        self.period_locked = False
        self.current_business_date = "2026-04-24" # Mock current date

    def lock_period(self):
        """Mandatory Night Audit Lock. Blocks all subsequent postings to the current period."""
        self.period_locked = True
        print(f"[FCE] PERIOD LOCKED: {self.current_business_date}. Night Audit Sealed.")

    def unlock_period(self, next_date: str):
        """Advances the business date and unlocks for new postings."""
        self.current_business_date = next_date
        self.period_locked = False
        print(f"[FCE] NEW PERIOD OPEN: {self.current_business_date}")

    def calculate_folio(
        self,
        base_amount: Decimal,
        pax: int = 1,
        nights: int = 1,
        stay_hours: float = 24.0,
        is_child: bool = False,
        effective_tgst: Decimal = None,
        biological_outcomes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Hardened MIRA Compliance Logic:
        1. Subtotal = Base
        2. TGST Transition: Use effective_tgst if provided.
        3. Green Tax 12-hour rule: $0 if stay < 12h.
        4. Child Exemption: Green Tax skip if is_child=True.
        """
        tgst_rate = effective_tgst if effective_tgst is not None else config.TGST

        # Integrate Biological ROI and ESG Regen Premium
        outcome_fees = Decimal("0.00")
        if biological_outcomes:
            recovered_hours = biological_outcomes.get("recovered_hours", 0)
            hourly_rate = biological_outcomes.get("recovered_hour_rate", Decimal("50.00"))
            outcome_fees += pricing_engine.calculate_recovered_hour_fee(recovered_hours, hourly_rate)

            healthspan_days = biological_outcomes.get("healthspan_gain_days", 0)
            dividend_rate = biological_outcomes.get("longevity_dividend_rate", Decimal("100.00"))
            outcome_fees += pricing_engine.calculate_longevity_dividend(healthspan_days, dividend_rate)

            regen_score = biological_outcomes.get("regen_score", 0)
            outcome_fees += pricing_engine.calculate_esg_regen_premium(regen_score, base_amount)

        subtotal = (base_amount + outcome_fees).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
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
        if self.period_locked:
            raise FinancialException("FCE: Period locked. Night Audit in progress or completed.")
        if amount > credit_limit:
            raise FinancialException(f"FCE AUTH DENIED: Amount {amount} exceeds limit {credit_limit} for folio {folio_id}")
        return True

    def process_reversal(self, original_entry_id: str, reason: str, ctx: Dict[str, Any]) -> str:
        """
        REVERSAL-ONLY DISCIPLINE:
        Never delete an entry. Create a contra-entry linked to the original.
        """
        from mnos.modules.shadow.service import shadow
        from mnos.shared.execution_guard import guard

        def reversal_logic(payload):
            return {"status": "REVERSED", "original_id": payload["original_id"]}

        res = guard.execute_sovereign_action(
            action_type="fce.ledger.reversal",
            payload={
                "original_id": original_entry_id,
                "reason": reason,
                "note": "COURT-VALID REVERSAL"
            },
            session_context=ctx,
            execution_logic=reversal_logic
        )
        print(f"[FCE] REVERSAL SEALED: Original Entry {original_entry_id}")
        return res["status"]

fce = FceService()

from decimal import Decimal
from typing import Dict, Any
from mnos.modules.fce.service import fce
from mnos.modules.shadow.service import shadow
from mnos.modules.elegal.packs.tenancy import tenancy_engine

class TenancyFinance:
    """
    Rent Financial Engine: Capturing the rent economy cashflow.
    Integrates Tenancy -> Legal Anchor -> SHADOW -> FCE -> Revenue.
    """
    def process_rent_payment(self, lease_id: str, amount: Decimal) -> Dict[str, Any]:
        """
        Processes a rent payment with mandatory eLEGAL anchor and TGST splitting.
        """
        lease = tenancy_engine.get_lease(lease_id)

        # 1. Calculate Folio with Maldives Tax logic via FCE
        # Rent is typically base, but FCE applies 10% SC + 17% TGST doctrine if applicable for commercial/managed
        # For simple residential, we might just track the base + TGST (if registered)
        folio = fce.calculate_folio(amount)

        # 2. Mandatory FCE Validation with Legal Anchor
        fce.validate_pre_auth(
            folio_id=f"RENT-{lease_id}",
            amount=amount,
            credit_limit=amount * 2, # Mocked credit limit
            legal_anchor_id=lease["anchor_id"]
        )

        payment_event = {
            "lease_id": lease_id,
            "anchor_id": lease["anchor_id"],
            "amount": str(amount),
            "folio": {k: str(v) if isinstance(v, Decimal) else v for k, v in folio.items()},
            "status": "PAID",
            "timestamp": datetime.now().isoformat()
        }

        shadow.commit("elegal.tenancy.rent_received", payment_event)
        return payment_event

    def hold_deposit_escrow(self, lease_id: str, amount: Decimal) -> Dict[str, Any]:
        lease = tenancy_engine.get_lease(lease_id)
        escrow_event = {
            "lease_id": lease_id,
            "anchor_id": lease["anchor_id"],
            "amount": str(amount),
            "status": "ESCROW_HELD"
        }
        shadow.commit("elegal.tenancy.rent_received", escrow_event)
        return escrow_event

from datetime import datetime
tenancy_finance = TenancyFinance()

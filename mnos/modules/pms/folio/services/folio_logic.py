from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
from mnos.modules.pms.folio.models.folio import Folio, FolioCharge, FolioPayment, ChargeReversal, ActorIdentityBundle
from decimal import Decimal
import uuid

class FolioLogic:
    """
    PMS Folio Logic: Orchestrates charges, payments, and state transitions.
    Enforces immutability and SHADOW auditing.
    """
    def __init__(self, billing_engine, guard, shadow, events):
        self.billing_engine = billing_engine
        self.guard = guard
        self.shadow = shadow
        self.events = events
        self.folios: Dict[str, Folio] = {} # id -> Folio
        self.charges: Dict[str, FolioCharge] = {} # id -> Charge

    def get_or_create_folio(self, guest_id: str, reservation_id: Optional[str] = None) -> Folio:
        # Search for open folio for guest
        for f in self.folios.values():
            if f.guest_id == guest_id and f.status in ["OPEN", "PARTIALLY_SETTLED"]:
                return f

        folio = Folio(guest_id=guest_id, reservation_id=reservation_id)
        self.folios[folio.id] = folio
        return folio

    def post_charge(self, actor_ctx: dict, folio_id: str, charge_data: dict) -> FolioCharge:
        """Atomic charge posting with forensic identity anchoring."""
        def _execute_charge():
            folio = self.folios.get(folio_id)
            if not folio: raise ValueError("Folio not found")
            if folio.status == "SEALED": raise ValueError("Folio is SEALED")

            # 1. Calculate pricing via Billing Engine
            pricing = self.billing_engine.calculate_charge(
                Decimal(str(charge_data["amount"])),
                category=charge_data.get("category", "ROOM"),
                green_tax_pax=charge_data.get("pax_count", 0),
                green_tax_nights=charge_data.get("nights", 0)
            )

            # 2. Build Forensic Identity Bundle
            identity = ActorIdentityBundle(
                staff_id=actor_ctx["identity_id"],
                role_id=actor_ctx["role"],
                device_id=actor_ctx["device_id"],
                aegis_context_id=str(uuid.uuid4()), # Simulated context link
                session_hash="HMAC-SESSION-PROOF",
                geo_location=charge_data.get("geo_location")
            )

            # 3. Create Charge record
            charge = FolioCharge(
                folio_id=folio_id,
                charge_type=charge_data.get("category", "ROOM"),
                description=charge_data["description"],
                unit_price=charge_data["amount"],
                subtotal=pricing["base"],
                service_charge_amount=pricing["service_charge"],
                tgst_amount=pricing["tax_amount"],
                green_tax_amount=pricing["green_tax_mvr"],
                line_total=pricing["total"],
                fx_rate=pricing["fx_rate"],
                actor_identity=identity
            )

            # 4. Update Folio balance
            folio.total_amount += charge.line_total
            folio.green_tax_total += charge.green_tax_amount
            folio.balance_due = folio.total_amount - folio.amount_paid
            folio.updated_at = datetime.now(UTC)

            self.charges[charge.id] = charge
            self.events.publish("pms.folio.charge_posted", charge.to_dict())
            return charge.to_dict()

        return self.guard.execute_sovereign_action(
            "pms.folio.post_charge",
            actor_ctx,
            _execute_charge
        )

    def reverse_charge(self, actor_ctx: dict, charge_id: str, reason_code: str, approver_id: str) -> FolioCharge:
        """Immutable reversal: Creates a negative entry. No deletes."""
        def _execute_reversal():
            orig = self.charges.get(charge_id)
            if not orig: raise ValueError("Original charge not found")
            if orig.is_reversal: raise ValueError("Charge is already a reversal")

            folio = self.folios.get(orig.folio_id)

            # Create negative charge
            reversal = orig.model_copy(deep=True)
            reversal.id = str(uuid.uuid4())
            reversal.description = f"REVERSAL: {orig.description}"
            reversal.unit_price = -orig.unit_price
            reversal.subtotal = -orig.subtotal
            reversal.service_charge_amount = -orig.service_charge_amount
            reversal.tgst_amount = -orig.tgst_amount
            reversal.green_tax_amount = -orig.green_tax_amount
            reversal.line_total = -orig.line_total
            reversal.is_reversal = True
            reversal.reversal_of_charge_id = orig.id
            reversal.posted_at = datetime.now(UTC)

            # Audit metadata
            rev_meta = ChargeReversal(
                original_charge_id=orig.id,
                reversal_charge_id=reversal.id,
                reason_code=reason_code,
                reason_detail="Reversal processed via FolioLogic",
                approved_by=approver_id,
                shadow_hash="PENDING"
            )

            # Update Folio
            folio.total_amount += reversal.line_total
            folio.green_tax_total += reversal.green_tax_amount
            folio.balance_due = folio.total_amount - folio.amount_paid

            self.charges[reversal.id] = reversal
            self.events.publish("pms.folio.charge_reversed", {"reversal": reversal.to_dict(), "meta": rev_meta.to_dict()})
            return reversal.to_dict()

        return self.guard.execute_sovereign_action(
            "pms.folio.reverse_charge",
            actor_ctx,
            _execute_reversal
        )

    def process_payment(self, actor_ctx: dict, folio_id: str, payment_data: dict) -> FolioPayment:
        """Processes partial or full settlement."""
        def _execute_payment():
            folio = self.folios.get(folio_id)
            if not folio: raise ValueError("Folio not found")

            amount = float(payment_data["amount"])

            identity = ActorIdentityBundle(
                staff_id=actor_ctx["identity_id"],
                role_id=actor_ctx["role"],
                device_id=actor_ctx["device_id"],
                aegis_context_id="SESSION-CTX",
                session_hash="PAYMENT-PROOF"
            )

            payment = FolioPayment(
                folio_id=folio_id,
                amount=amount,
                method=payment_data["method"],
                fx_rate=float(self.billing_engine.locked_fx_rate),
                actor_identity=identity
            )

            folio.amount_paid += payment.amount
            folio.balance_due = float(Decimal(str(folio.total_amount)) - Decimal(str(folio.amount_paid)))
            folio.last_payment_at = datetime.now(UTC)

            if folio.balance_due <= 0.01: # Account for float
                folio.status = "SETTLED"
                folio.balance_due = 0.0
            else:
                folio.status = "PARTIALLY_SETTLED"

            self.events.publish("pms.folio.payment_captured", payment.to_dict())
            return payment.to_dict()

        return self.guard.execute_sovereign_action(
            "pms.folio.process_payment",
            actor_ctx,
            _execute_payment
        )

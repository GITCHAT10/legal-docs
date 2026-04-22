from typing import Dict, Optional, Any
from sqlalchemy.orm import Session
from decimal import Decimal, ROUND_HALF_UP
import uuid
import json
from datetime import datetime, timezone

from mnos.modules.fce import models
from mnos.modules.shadow.service import shadow
from mnos.config import config

class FinancialException(Exception):
    pass

class FceService:
    """
    Financial Control Engine: Maldives-native tax logic and fiscal settlement.
    """
    def calculate_folio(self, base_amount: Decimal, pax: int = 1, nights: int = 1) -> Dict[str, Any]:
        """Legacy compatibility wrapper."""
        return self.calculate_taxes(base_amount, pax, nights, apply_green_tax=True)

    def calculate_taxes(self, base_amount: Decimal, pax: int = 1, nights: int = 1, apply_green_tax: bool = False) -> Dict[str, Any]:
        """
        Strict MOATS tax logic implementation:
        1. Subtotal = Base
        2. Service Charge = 10% of Subtotal
        3. TGST = 17% of (Subtotal + Service Charge)
        4. Green Tax = $6 * pax * nights (if applicable)
        """
        subtotal = base_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        service_charge = (subtotal * config.SERVICE_CHARGE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        taxable_amount = subtotal + service_charge
        tgst = (taxable_amount * config.TGST).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        green_tax = Decimal("0.00")
        if apply_green_tax:
            green_tax = (config.GREEN_TAX_USD * Decimal(pax) * Decimal(nights)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total = taxable_amount + tgst + green_tax

        return {
            "base": subtotal,
            "service_charge": service_charge,
            "taxable_amount": taxable_amount,
            "tgst": tgst,
            "green_tax": green_tax,
            "total": total,
            "total_amount": total, # Compatibility
            "base_amount": subtotal, # Compatibility
            "currency": "USD"
        }

    def preauthorize(self, db: Session, actor_id: str, amount: Decimal) -> bool:
        """FCE Financial Gate: Check if the actor is authorized for the amount."""
        if amount > Decimal("50000.00"):
             return False
        return True

    def validate_pre_auth(self, folio_id: str, amount: Decimal, credit_limit: Decimal) -> bool:
        """Mandatory validation before commit."""
        if amount > credit_limit:
            raise FinancialException(f"FCE AUTH DENIED: Amount {amount} exceeds limit {credit_limit} for folio {folio_id}")
        return True

    def open_folio(self, db: Session, reservation_id: str, trace_id: str) -> models.Folio:
        """Atomic Folio Creation with Idempotency."""
        existing = db.query(models.Folio).filter(models.Folio.trace_id == trace_id).first()
        if existing:
            return existing

        folio = models.Folio(
            external_reservation_id=reservation_id,
            trace_id=trace_id,
            status=models.FolioStatus.OPEN
        )
        db.add(folio)

        self._log_event(db, "FOLIO_OPENED", {"reservation_id": reservation_id}, trace_id)
        db.commit()
        db.refresh(folio)
        return folio

    def post_charge(self, db: Session, folio_id: int, charge_data: Dict, trace_id: str) -> models.FolioLine:
        """Atomic Charge Posting with MIRA Tax Logic and SHADOW write."""
        existing = db.query(models.FolioLine).filter(models.FolioLine.trace_id == trace_id).first()
        if existing:
            return existing

        taxes = self.calculate_taxes(
            Decimal(str(charge_data["base_amount"])),
            pax=charge_data.get("pax", 1),
            nights=charge_data.get("nights", 1),
            apply_green_tax=charge_data.get("apply_green_tax", False)
        )

        line = models.FolioLine(
            folio_id=folio_id,
            trace_id=trace_id,
            type=charge_data["type"],
            base_amount=taxes["base_amount"],
            service_charge=taxes["service_charge"],
            tgst=taxes["tgst"],
            green_tax=taxes["green_tax"],
            total_amount=taxes["total_amount"],
            description=charge_data.get("description")
        )
        db.add(line)

        folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
        folio.total_amount += line.total_amount

        shadow.commit("CHARGE_POSTED", {"folio_id": folio_id, "amount": str(line.total_amount), "trace_id": trace_id})
        self._log_event(db, "CHARGE_POSTED", {"folio_id": folio_id, "amount": str(line.total_amount)}, trace_id)

        db.commit()
        db.refresh(line)
        return line

    def process_payment(self, db: Session, folio_id: int, payment_data: Dict, trace_id: str) -> models.Payment:
        """Atomic Payment Processing."""
        existing = db.query(models.Payment).filter(models.Payment.trace_id == trace_id).first()
        if existing:
            return existing

        payment = models.Payment(
            folio_id=folio_id,
            trace_id=trace_id,
            amount=Decimal(str(payment_data["amount"])),
            method=payment_data["method"],
            status=models.PaymentStatus.PAID
        )
        db.add(payment)

        folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
        folio.paid_amount += payment.amount

        if folio.paid_amount >= folio.total_amount:
            folio.status = models.FolioStatus.FINALIZED

        ledger = models.LedgerEntry(
            trace_id=f"ledger-{trace_id}",
            account_code="CASH_CC",
            debit=payment.amount,
            description=f"Payment for folio {folio_id}"
        )
        db.add(ledger)

        shadow.commit("PAYMENT_PROCESSED", {"folio_id": folio_id, "amount": str(payment.amount), "trace_id": trace_id})
        self._log_event(db, "PAYMENT_RECEIVED", {"folio_id": folio_id, "amount": str(payment.amount)}, trace_id)

        db.commit()
        db.refresh(payment)
        return payment

    def finalize_invoice(self, db: Session, folio_id: int, trace_id: str, actor_id: str = "SYSTEM") -> models.Folio:
        """
        Directive: Implement finalize_invoice.
        Must pull all FolioLine entries, calculate MIRA-compliant GST, and seal in SHADOW.
        """
        folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
        if not folio:
            raise FinancialException(f"Folio {folio_id} not found.")

        if folio.status == models.FolioStatus.FINALIZED:
            return folio

        # In this architecture, taxes are calculated per line at post_charge.
        # Finalization ensures all lines are reconciled and the ledger is sealed.

        folio.status = models.FolioStatus.FINALIZED

        # Directive: Audit via SAL (which seals in SHADOW)
        from mnos.core.audit.sal import sal
        sal.log(
            trace_id=trace_id,
            actor_identity=actor_id,
            event_type="INVOICE_FINALIZED",
            payload={
                "folio_id": folio_id,
                "total_amount": str(folio.total_amount),
                "paid_amount": str(folio.paid_amount),
                "tax_breakdown": {
                    "tgst": str(sum(l.tgst for l in folio.lines)),
                    "service_charge": str(sum(l.service_charge for l in folio.lines)),
                    "green_tax": str(sum(l.green_tax for l in folio.lines))
                }
            }
        )

        self._log_event(db, "INVOICE_FINALIZED", {"folio_id": folio_id}, trace_id)

        db.commit()
        db.refresh(folio)
        return folio

    def _log_event(self, db: Session, event_type: str, payload: Dict, trace_id: str):
        outbox = models.OutboxEvent(
            event_type=event_type,
            payload=json.dumps(payload),
            trace_id=f"evt-{trace_id}"
        )
        db.add(outbox)

fce = FceService()

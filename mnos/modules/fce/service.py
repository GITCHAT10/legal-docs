from typing import Dict, Optional, Any
from sqlalchemy.orm import Session
from decimal import Decimal
import uuid
import json

from mnos.modules.fce import models, tax_logic
from mnos.modules.shadow import service as shadow_service

def preauthorize(db: Session, actor_id: str, amount: Decimal | float) -> bool:
    """
    FCE Financial Gate: Check if the actor is authorized for the amount
    and if fiscal rules permit the transaction.
    """
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    # Placeholder for credit limit/policy check
    if amount > Decimal("50000.00"):
         return False

    return True

def open_folio(db: Session, reservation_id: str, trace_id: str) -> models.Folio:
    """
    Atomic Folio Creation with Idempotency.
    """
    existing = db.query(models.Folio).filter(models.Folio.trace_id == trace_id).first()
    if existing:
        return existing

    try:
        folio = models.Folio(
            external_reservation_id=reservation_id,
            trace_id=trace_id,
            status=models.FolioStatus.OPEN
        )
        db.add(folio)

        outbox = models.OutboxEvent(
            event_type="FOLIO_OPENED",
            payload={"reservation_id": reservation_id, "trace_id": trace_id},
            trace_id=f"evt-{trace_id}"
        )
        db.add(outbox)

        db.commit()
        db.refresh(folio)
        return folio
    except Exception as e:
        db.rollback()
        raise e

def post_charge(db: Session, folio_id: int, charge_data: Dict, trace_id: str) -> models.FolioLine:
    """
    Atomic Charge Posting with MIRA Tax Logic and SHADOW write.
    """
    existing = db.query(models.FolioLine).filter(models.FolioLine.trace_id == trace_id).first()
    if existing:
        return existing

    try:
        taxes = tax_logic.calculate_maldives_taxes(
            charge_data["base_amount"],
            charge_data.get("apply_green_tax", False),
            charge_data.get("nights", 0)
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
        db.add(folio)

        # Atomic SHADOW Write (Part of the transaction)
        shadow_service.commit_evidence(db, trace_id, {
            "action": "CHARGE_POSTED",
            "folio_id": folio_id,
            "amount": str(line.total_amount)
        })

        outbox = models.OutboxEvent(
            event_type="CHARGE_POSTED",
            payload={"folio_id": folio_id, "amount": str(line.total_amount)},
            trace_id=f"evt-{trace_id}"
        )
        db.add(outbox)

        db.commit()
        db.refresh(line)
        return line
    except Exception as e:
        db.rollback()
        raise e

def process_payment(db: Session, folio_id: int, payment_data: Dict, trace_id: str) -> models.Payment:
    """
    Atomic Payment Processing with Fail-Closed status.
    """
    existing = db.query(models.Payment).filter(models.Payment.trace_id == trace_id).first()
    if existing:
        return existing

    try:
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

        db.add(folio)

        ledger = models.LedgerEntry(
            trace_id=f"ledger-{trace_id}",
            account_code="CASH_CC",
            debit=payment.amount,
            description=f"Payment for folio {folio_id}"
        )
        db.add(ledger)

        # Shadow audit
        shadow_service.commit_evidence(db, trace_id, {
            "action": "PAYMENT_PROCESSED",
            "folio_id": folio_id,
            "amount": str(payment.amount)
        })

        outbox = models.OutboxEvent(
            event_type="PAYMENT_RECEIVED",
            payload={"folio_id": folio_id, "amount": str(payment.amount)},
            trace_id=f"evt-{trace_id}"
        )
        db.add(outbox)

        db.commit()
        db.refresh(payment)
        return payment
    except Exception as e:
        db.rollback()
        # Persist a PENDING_RECONCILIATION record on failure if amount was potentially moved
        error_trace = f"err-{trace_id}-{uuid.uuid4().hex[:4]}"
        try:
            recovery_payment = models.Payment(
                folio_id=folio_id,
                trace_id=trace_id,
                amount=Decimal(str(payment_data["amount"])),
                method=payment_data["method"],
                status=models.PaymentStatus.PENDING_RECONCILIATION
            )
            db.add(recovery_payment)
            db.commit()
            return recovery_payment
        except:
            db.rollback()
            raise e

def flush_outbox(db: Session):
    events = db.query(models.OutboxEvent).filter(models.OutboxEvent.processed == False).all()
    for event in events:
        event.processed = True
        db.add(event)
    db.commit()

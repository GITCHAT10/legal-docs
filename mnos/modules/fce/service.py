from typing import Dict, Optional, Any
from sqlalchemy.orm import Session
from decimal import Decimal
import uuid
import json

from mnos.modules.fce import models, tax_logic
from mnos.modules.shadow import service as shadow_service

def open_folio(db: Session, reservation_id: str, trace_id: str) -> models.Folio:
    """
    Atomic Folio Creation with Idempotency.
    """
    # 1. Idempotency Check
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

        # 2. Outbox Event
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
    # 1. Idempotency Check
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

        # 2. Atomic SHADOW Write (Simulation within transaction)
        shadow_service.commit_evidence(db, trace_id, {
            "action": "CHARGE_POSTED",
            "folio_id": folio_id,
            "amount": float(line.total_amount)
        })

        # 3. Outbox Event
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
    # 1. Idempotency Check
    existing = db.query(models.Payment).filter(models.Payment.trace_id == trace_id).first()
    if existing:
        return existing

    try:
        payment = models.Payment(
            folio_id=folio_id,
            trace_id=trace_id,
            amount=Decimal(str(payment_data["amount"])),
            method=payment_data["method"],
            status=models.PaymentStatus.PAID # Assuming gateway success for this flow
        )
        db.add(payment)

        folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
        folio.paid_amount += payment.amount

        if folio.paid_amount >= folio.total_amount:
            folio.status = models.FolioStatus.FINALIZED # Using FINALIZED as PAID status for Folio

        db.add(folio)

        # 2. Ledger Entry
        ledger = models.LedgerEntry(
            trace_id=f"ledger-{trace_id}",
            account_code="CASH_CC",
            debit=payment.amount,
            description=f"Payment for folio {folio_id}"
        )
        db.add(ledger)

        # 3. Outbox Event
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
        # In case of gateway success but ledger failure
        return models.Payment(
            folio_id=folio_id,
            trace_id=trace_id,
            amount=Decimal(str(payment_data["amount"])),
            method=payment_data["method"],
            status=models.PaymentStatus.PENDING_RECONCILIATION
        )

def flush_outbox(db: Session):
    """
    Simulated reliable event dispatcher.
    """
    events = db.query(models.OutboxEvent).filter(models.OutboxEvent.processed == False).all()
    for event in events:
        # In real life: publish to RabbitMQ/Redis
        event.processed = True
        db.add(event)
    db.commit()

from typing import Dict, Optional
from sqlalchemy.orm import Session
from mnos.modules.fce import models
import uuid
from datetime import datetime
from .tax_logic import calculate_maldives_tax

def open_folio(db: Session, reservation_id: str, trace_id: str) -> models.Folio:
    existing = db.query(models.Folio).filter(models.Folio.trace_id == trace_id).first()
    if existing:
        return existing

    folio = models.Folio(
        external_reservation_id=reservation_id,
        trace_id=trace_id,
        status=models.FolioStatus.OPEN
    )
    db.add(folio)
    db.commit()
    db.refresh(folio)
    return folio

def post_charge(db: Session, folio_id: int, charge_data: Dict, trace_id: str) -> models.FolioLine:
    existing = db.query(models.FolioLine).filter(models.FolioLine.trace_id == trace_id).first()
    if existing:
        return existing

    taxes = calculate_maldives_tax(
        charge_data["base_amount"],
        charge_data.get("apply_green_tax", False),
        charge_data.get("nights", 0)
    )

    line = models.FolioLine(
        folio_id=folio_id,
        trace_id=trace_id,
        type=charge_data["type"],
        base_amount=taxes["base"],
        service_charge=taxes["service_charge"],
        tgst=taxes["tgst"],
        green_tax=taxes["green_tax"],
        amount=taxes["total"],
        description=charge_data.get("description")
    )
    db.add(line)

    folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
    folio.total_amount += line.amount
    db.add(folio)

    # Record in ledger
    ledger = models.LedgerEntry(
        trace_id=f"ledger-{trace_id}",
        account_code="REVENUE",
        credit=line.amount,
        description=f"Charge for folio {folio_id}"
    )
    db.add(ledger)

    db.commit()
    db.refresh(line)
    return line

def post_payment(db: Session, folio_id: int, payment_data: Dict, trace_id: str) -> models.Payment:
    existing = db.query(models.Payment).filter(models.Payment.trace_id == trace_id).first()
    if existing:
        return existing

    payment = models.Payment(
        folio_id=folio_id,
        trace_id=trace_id,
        amount=payment_data["amount"],
        method=payment_data["method"],
        status=payment_data.get("status", models.PaymentStatus.PAID)
    )
    db.add(payment)

    folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()
    folio.paid_amount += payment.amount
    db.add(folio)

    db.commit()
    db.refresh(payment)
    return payment

def finalize_invoice(db: Session, folio_id: int) -> models.Invoice:
    folio = db.query(models.Folio).filter(models.Folio.id == folio_id).first()

    invoice = models.Invoice(
        folio_id=folio_id,
        invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
        total_amount=folio.total_amount,
        tax_summary={
            "sc": sum(l.service_charge for l in folio.lines),
            "tgst": sum(l.tgst for l in folio.lines),
            "green_tax": sum(l.green_tax for l in folio.lines)
        }
    )
    db.add(invoice)
    folio.status = models.FolioStatus.FINALIZED
    db.add(folio)
    db.commit()
    db.refresh(invoice)
    return invoice

def lock_exchange_rate(db: Session, currency: str, rate: float, expires_at: datetime) -> models.ExchangeRateLock:
    lock = models.ExchangeRateLock(
        currency=currency,
        rate=rate,
        expires_at=expires_at
    )
    db.add(lock)
    db.commit()
    db.refresh(lock)
    return lock

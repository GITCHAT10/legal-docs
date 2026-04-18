from sqlalchemy.orm import Session
from .models import FinanceEventModel, PayoutBatchModel, LedgerModel
from skyfarm.integration.outbox_service import queue_event
import uuid
from typing import Dict, Any

def calculate_maldives_pricing(base_price: float):
    service_charge = base_price * 0.10
    subtotal = base_price + service_charge
    tgst = subtotal * 0.17
    total = subtotal + tgst
    return {
        "base": round(base_price, 2),
        "service_charge": round(service_charge, 2),
        "subtotal": round(subtotal, 2),
        "tgst": round(tgst, 2),
        "total": round(total, 2)
    }

def capture_payment(db: Session, amount: float, reference_id: str, tenant_id: str, currency: str = "USD"):
    event = FinanceEventModel(
        id=f"fin_{uuid.uuid4().hex[:8]}",
        type="payout.batch.approved",
        amount=amount,
        currency=currency,
        reference_id=reference_id
    )
    db.add(event)

    # Record in Ledger
    ledger = LedgerModel(
        id=f"ldgr_{uuid.uuid4().hex[:8]}",
        account_id=tenant_id,
        type="credit",
        amount=amount,
        reference_id=reference_id
    )
    db.add(ledger)

    # Queue event for MNOS
    queue_event(db, tenant_id, "payout.batch.approved", {
        "amount": amount,
        "currency": currency,
        "reference_id": reference_id
    })

    db.commit()
    db.refresh(event)
    return event

def generate_invoice_data(base_price: float, reference_id: str):
    pricing = calculate_maldives_pricing(base_price)
    return {
        "invoice_id": f"INV-{uuid.uuid4().hex[:6].upper()}",
        "reference_id": reference_id,
        "pricing": pricing,
        "currency": "MVR"
    }

def create_payout_batch(db: Session, amount: float, tenant_id: str):
    batch = PayoutBatchModel(
        id=f"pb_{uuid.uuid4().hex[:8]}",
        total_amount=amount,
        status="pending"
    )
    db.add(batch)

    # Ledger debit for payout prep
    ledger = LedgerModel(
        id=f"ldgr_{uuid.uuid4().hex[:8]}",
        account_id=tenant_id,
        type="debit",
        amount=amount,
        reference_id=batch.id
    )
    db.add(ledger)

    db.commit()
    db.refresh(batch)
    return batch

from sqlalchemy.orm import Session
from .models import FinanceEventModel
from skyfarm.integration.outbox_service import queue_event
import uuid

def capture_payment(db: Session, amount: float, reference_id: str, tenant_id: str, currency: str = "USD"):
    event = FinanceEventModel(
        id=f"fin_{uuid.uuid4().hex[:8]}",
        type="payout.batch.approved",
        amount=amount,
        currency=currency,
        reference_id=reference_id
    )
    db.add(event)

    # Queue event for MNOS
    queue_event(db, tenant_id, "payout.batch.approved", {
        "amount": amount,
        "currency": currency,
        "reference_id": reference_id
    })

    db.commit()
    db.refresh(event)
    return event

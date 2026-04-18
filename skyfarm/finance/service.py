from sqlalchemy.orm import Session
from .models import FinanceEventModel
import uuid

def capture_payment(db: Session, amount: float, reference_id: str, currency: str = "USD"):
    event = FinanceEventModel(
        id=f"fin_{uuid.uuid4().hex[:8]}",
        type="PAYMENT_CAPTURED",
        amount=amount,
        currency=currency,
        reference_id=reference_id
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def record_item_sold(db: Session, amount: float, reference_id: str):
    event = FinanceEventModel(
        id=f"fin_{uuid.uuid4().hex[:8]}",
        type="ITEM_SOLD",
        amount=amount,
        reference_id=reference_id
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

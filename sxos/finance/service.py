from sqlalchemy.orm import Session
from .models import SettlementModel
import uuid

def process_settlement(db: Session, tenant_id: str, transaction_id: str, total_amount: float):
    margin = total_amount * 0.15
    yield_val = total_amount - margin

    distributions = [
        {"party": "supplier", "amount": total_amount * 0.65},
        {"party": "government", "amount": total_amount * 0.17},
        {"party": "logistics", "amount": total_amount * 0.10},
        {"party": "system", "amount": margin}
    ]

    settlement = SettlementModel(
        transaction_id=transaction_id,
        tenant_id=tenant_id,
        amount=total_amount,
        margin=margin,
        yield_amount=yield_val,
        distributions=distributions,
        status="COMPLETED"
    )
    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement

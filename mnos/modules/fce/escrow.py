from sqlalchemy.orm import Session
from decimal import Decimal
from . import models
from mnos.modules.shadow import service as shadow_service

def lock_funds(db: Session, trace_id: str, amount: float, currency: str = "MVR"):
    # Mock escrow lock
    shadow_service.commit_evidence(db, trace_id, {
        "action": "ESCROW_LOCK",
        "amount": amount,
        "currency": currency,
        "status": "LOCKED"
    })
    db.commit()
    return True

def release_funds(db: Session, trace_id: str, event_verified: bool):
    if not event_verified:
        return False

    # Requirement: NO_RELEASE_WITHOUT_SHADOW_COMMIT
    shadow_service.commit_evidence(db, trace_id, {
        "action": "ESCROW_RELEASE",
        "status": "RELEASED"
    })
    db.commit()
    return True

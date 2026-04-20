import hashlib
import json
from sqlalchemy.orm import Session
from mnos.modules.shadow import models

def commit_evidence(db: Session, trace_id: str, payload: dict) -> models.Evidence:
    # Get last evidence for chaining
    last = db.query(models.Evidence).order_by(models.Evidence.id.desc()).first()
    prev_hash = last.current_hash if last else "0" * 64

    # payload_digest
    payload_str = json.dumps(payload, sort_keys=True)
    payload_digest = hashlib.sha256(payload_str.encode()).hexdigest()

    # current_hash = prev_hash + payload_digest + trace_id
    combined = f"{prev_hash}{payload_digest}{trace_id}"
    current_hash = hashlib.sha256(combined.encode()).hexdigest()

    evidence = models.Evidence(
        trace_id=trace_id,
        actor=payload.get("actor", "SYSTEM"),
        action=payload.get("action", "STATE_CHANGE"),
        entity_type=payload.get("entity_type"),
        entity_id=str(payload.get("entity_id")) if payload.get("entity_id") else None,
        before_state=payload.get("before_state"),
        after_state=payload.get("after_state"),
        payload=payload,
        previous_hash=prev_hash,
        payload_digest=payload_digest,
        current_hash=current_hash
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence

def fetch_evidence(db: Session, trace_id: str):
    return db.query(models.Evidence).filter(models.Evidence.trace_id == trace_id).first()

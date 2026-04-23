import hashlib
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from mnos.core.shadow import models

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
    db.flush()
    return evidence

def fetch_evidence(db: Session, trace_id: str):
    return db.query(models.Evidence).filter(models.Evidence.trace_id == trace_id).first()

def verify_chain(db: Session) -> Dict[str, Any]:
    """
    Forensic Chain Verification.
    Detects any tampering in the SHADOW ledger.
    """
    evidences = db.query(models.Evidence).order_by(models.Evidence.id.asc()).all()

    if not evidences:
        return {"status": "empty", "verified": True}

    prev_hash = "0" * 64
    tampered_ids = []

    for ev in evidences:
        # Recompute digest
        payload_str = json.dumps(ev.payload, sort_keys=True)
        recomputed_digest = hashlib.sha256(payload_str.encode()).hexdigest()

        # Recompute hash
        combined = f"{prev_hash}{recomputed_digest}{ev.trace_id}"
        recomputed_hash = hashlib.sha256(combined.encode()).hexdigest()

        if recomputed_hash != ev.current_hash or ev.previous_hash != prev_hash:
            tampered_ids.append(ev.id)

        prev_hash = ev.current_hash

    return {
        "status": "compromised" if tampered_ids else "secure",
        "verified": len(tampered_ids) == 0,
        "tampered_entries": tampered_ids,
        "total_entries": len(evidences)
    }

def replay_state(db: Session, entity_type: str, entity_id: str) -> Dict[str, Any]:
    """
    Forensic Replay: Reconstruct an entity's state history from SHADOW.
    """
    logs = db.query(models.Evidence).filter(
        models.Evidence.entity_type == entity_type,
        models.Evidence.entity_id == entity_id
    ).order_by(models.Evidence.created_at.asc()).all()

    history = []
    for log in logs:
        history.append({
            "timestamp": log.created_at.isoformat(),
            "actor": log.actor,
            "action": log.action,
            "before": log.before_state,
            "after": log.after_state
        })

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "history": history
    }

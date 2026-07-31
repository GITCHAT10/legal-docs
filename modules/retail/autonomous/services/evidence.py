from sqlalchemy.orm import Session
from ..models.database import RetailSession, RetailSessionEvent, RetailSessionCartItem, RetailHardwareNode
from typing import Dict, Any
import hashlib
import json
import uuid

async def build_shadow_evidence_envelope(db: Session, session_id: str) -> Dict[str, Any]:
    session_uuid = uuid.UUID(session_id)
    session = db.query(RetailSession).filter(RetailSession.id == session_uuid).first()
    if not session:
        return {}

    events = db.query(RetailSessionEvent).filter(RetailSessionEvent.session_id == session_uuid).order_by(RetailSessionEvent.created_at).all()
    cart_items = db.query(RetailSessionCartItem).filter(RetailSessionCartItem.session_id == session_uuid).all()

    # Timeline of sensor events
    event_timeline = [
        {
            "timestamp": e.created_at.isoformat(),
            "type": e.event_type,
            "source": e.source,
            "hardware_id": e.hardware_id,
            "product_id": e.product_id,
            "qty": float(e.qty) if e.qty else 0,
            "confidence": float(e.confidence),
            "trust_score": float(e.trust_score_at_event) if e.trust_score_at_event else 1.0,
            "is_duplicate": e.is_duplicate
        } for e in events
    ]

    # Final cart state
    final_cart = [
        {
            "product_id": item.product_id,
            "qty": float(item.qty),
            "unit_price": float(item.unit_price),
            "subtotal": float(item.subtotal),
            "price_snapshot": item.price_snapshot,
            "confidence": float(item.confidence_score),
            "anomalies": item.anomaly_flags
        } for item in cart_items
    ]

    evidence = {
        "metadata": {
            "tenant_id": str(session.tenant_id),
            "trace_id": str(session.trace_id),
            "session_id": str(session.id),
            "store_id": session.store_id,
            "aegis_user_id": str(session.aegis_user_id)
        },
        "lifecycle": {
            "entry_time": session.entry_time.isoformat() if session.entry_time else None,
            "exit_time": session.exit_time.isoformat() if session.exit_time else None,
            "status": session.status
        },
        "sensor_evidence": {
            "event_timeline": event_timeline,
            "total_events": len(events)
        },
        "cart_evidence": {
            "items": final_cart,
            "final_confidence": float(session.confidence_score) if session.confidence_score else None,
            "anomaly_flags": session.anomaly_flags
        },
        "settlement_evidence": {
            "settlement_id": str(session.settlement_id) if session.settlement_id else None,
            "receipt_id": session.receipt_id,
            "idempotency_key": session.idempotency_key
        },
        "audit_history": {
            "reviewer_id": str(session.reviewer_id) if session.reviewer_id else None,
            "review_reason": session.review_reason,
            "parent_session_id": str(session.parent_session_id) if session.parent_session_id else None
        }
    }

    # Calculate integrity checksum
    evidence_json = json.dumps(evidence, sort_keys=True)
    integrity_checksum = hashlib.sha256(evidence_json.encode()).hexdigest()
    evidence["integrity_checksum"] = integrity_checksum

    return evidence

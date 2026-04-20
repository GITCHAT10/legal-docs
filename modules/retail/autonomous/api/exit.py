from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..models.schemas import SessionExitRequest, FCESettleResponse
from ..models.database import RetailSession, RetailSessionCartItem, get_db
from ..services.adapters import FCEAdapter, EVENTSAdapter, SHADOWAdapter, INNAdapter
from ..services.security import verify_signed_credentials
from ..services.evidence import build_shadow_evidence_envelope
from ..events.contracts import EVENT_SESSION_EXITED, EVENT_SESSION_SETTLED, EVENT_SESSION_FLAGGED
from decimal import Decimal
import uuid
from datetime import datetime, timezone

router = APIRouter(dependencies=[Depends(verify_signed_credentials)])

HIGH_CONFIDENCE_THRESHOLD = Decimal("0.95")
REVIEW_THRESHOLD = Decimal("0.90")

@router.post("/session/exit")
async def exit_session(request: SessionExitRequest, db: Session = Depends(get_db)):
    fce = FCEAdapter()
    events = EVENTSAdapter()
    shadow = SHADOWAdapter()
    inn = INNAdapter()

    session_id = request.session_id

    # 1. Load and lock session to prevent duplicate/concurrent exit processing
    session_record = db.query(RetailSession).with_for_update().filter(RetailSession.id == session_id).first()
    if not session_record:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if already settled or exited
    if session_record.status in ["SETTLED", "EXITED"]:
        return {
            "session_id": session_id,
            "status": session_record.status,
            "settlement_id": session_record.settlement_id,
            "receipt_id": session_record.receipt_id,
            "message": "Session already processed"
        }

    # 2. Compute final cart and confidence
    cart_items = db.query(RetailSessionCartItem).filter(RetailSessionCartItem.session_id == session_id).all()
    if not cart_items:
        avg_confidence = Decimal("1.0")
    else:
        avg_confidence = sum(item.confidence_score for item in cart_items) / len(cart_items)

    # Collect session-level anomaly flags
    current_session_flags = session_record.anomaly_flags or []
    for item in cart_items:
        if item.anomaly_flags:
            current_session_flags.extend(item.anomaly_flags)
    session_record.anomaly_flags = list(set(current_session_flags))

    base_amount = sum(item.subtotal for item in cart_items)

    # 3. Apply confidence policy
    status = "EXITED"
    settlement_result = None

    if avg_confidence >= HIGH_CONFIDENCE_THRESHOLD and not session_record.anomaly_flags:
        # Resolve payment destination (Room Folio or Default)
        folio_id = await inn.resolve_active_folio(str(session_record.aegis_user_id), str(session_record.tenant_id))

        # Auto-settle via FCE with Idempotency
        idempotency_key = f"retail-exit-{session_id}"
        settle_payload = {
            "tenant_id": str(session_record.tenant_id),
            "aegis_user_id": str(session_record.aegis_user_id),
            "session_id": str(session_id),
            "trace_id": str(session_record.trace_id),
            "source_module": "A_RETAIL",
            "idempotency_key": idempotency_key,
            "folio_id": folio_id,
            "items": [
                {
                    "product_id": item.product_id,
                    "qty": float(item.qty),
                    "unit_price": float(item.unit_price),
                    "subtotal": float(item.subtotal),
                    "price_snapshot": item.price_snapshot
                } for item in cart_items
            ],
            "base_amount": float(base_amount),
            "fee_profile": "AUTONOMOUS_RETAIL_STANDARD"
        }

        try:
            settlement_result = await fce.settle_autonomous(settle_payload)
            session_record.status = "SETTLED"
            session_record.settlement_id = uuid.UUID(settlement_result["settlement_id"])
            session_record.receipt_id = settlement_result["receipt_id"]
            session_record.idempotency_key = idempotency_key
            status = "SETTLED"

            await events.publish(EVENT_SESSION_SETTLED, {
                "session_id": str(session_id),
                "settlement_id": settlement_result["settlement_id"],
                "receipt_id": settlement_result["receipt_id"]
            })
        except Exception as e:
            session_record.status = "FLAGGED"
            status = "FLAGGED"
            await events.publish(EVENT_SESSION_FLAGGED, {
                "session_id": str(session_id),
                "reason": f"Settlement failed: {str(e)}"
            })

    elif avg_confidence >= REVIEW_THRESHOLD:
        session_record.status = "FLAGGED"
        status = "FLAGGED"
        await events.publish(EVENT_SESSION_FLAGGED, {
            "session_id": str(session_id),
            "reason": "LOW_CONFIDENCE_REVIEW"
        })
    else:
        session_record.status = "FLAGGED"
        status = "FLAGGED"
        await events.publish(EVENT_SESSION_FLAGGED, {
            "session_id": str(session_id),
            "reason": "CRITICAL_CONFIDENCE_FAILURE"
        })

    session_record.exit_time = datetime.now(timezone.utc)
    session_record.confidence_score = avg_confidence
    db.commit()

    # 4. Commit SHADOW evidence package
    evidence_bundle = await build_shadow_evidence_envelope(db, str(session_id))
    session_record.evidence_bundle = evidence_bundle
    db.commit()

    shadow_hash = await shadow.commit({
        "tenant_id": str(session_record.tenant_id),
        "trace_id": str(session_record.trace_id),
        "entity_type": "A_RETAIL_SESSION",
        "entity_id": str(session_id),
        "event_type": status,
        "payload": evidence_bundle
    })
    session_record.shadow_hash = shadow_hash
    db.commit()

    return {
        "session_id": session_id,
        "status": status,
        "settlement_id": session_record.settlement_id,
        "receipt_id": session_record.receipt_id
    }

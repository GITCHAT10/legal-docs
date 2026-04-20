from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..models.database import RetailSession, RetailSessionCartItem, get_db
from ..services.adapters import FCEAdapter, EVENTSAdapter, SHADOWAdapter, INNAdapter, AEGISAdapter
from ..services.security import verify_signed_credentials
from ..services.evidence import build_shadow_evidence_envelope
from ..events.contracts import EVENT_SESSION_SETTLED, EVENT_SESSION_CANCELLED
import uuid
from decimal import Decimal

router = APIRouter(dependencies=[Depends(verify_signed_credentials)])

ESCALATION_THRESHOLD = Decimal("500.00")

class ReviewActionRequest(BaseModel):
    session_id: uuid.UUID
    action: str # APPROVE, CANCEL, REVERSE
    reason: str
    reviewer_token: str # To verify actor via AEGIS

@router.post("/review/resolve")
async def resolve_flagged_session(request: ReviewActionRequest, db: Session = Depends(get_db)):
    fce = FCEAdapter()
    events = EVENTSAdapter()
    shadow = SHADOWAdapter()
    inn = INNAdapter()
    aegis = AEGISAdapter()

    # 1. Verify reviewer identity
    reviewer_result = await aegis.validate_token(request.reviewer_token)
    if not reviewer_result.get("valid"):
        raise HTTPException(status_code=401, detail="Invalid reviewer credentials")
    reviewer_id = uuid.UUID(reviewer_result["aegis_user_id"])

    # 2. Load and lock session
    session_id = request.session_id
    session_record = db.query(RetailSession).with_for_update().filter(RetailSession.id == session_id).first()
    if not session_record:
        raise HTTPException(status_code=404, detail="Session not found")

    cart_items = db.query(RetailSessionCartItem).filter(RetailSessionCartItem.session_id == session_id).all()
    total_amount = sum(item.subtotal for item in cart_items)

    # 3. Escalation check
    if total_amount > ESCALATION_THRESHOLD:
        # In production: check if reviewer has supervisor role
        pass

    session_record.reviewer_id = reviewer_id
    session_record.review_reason = request.reason

    if request.action == "APPROVE":
        if session_record.status == "SETTLED":
             raise HTTPException(status_code=400, detail="Already settled")

        # Resolve folio if available
        folio_id = await inn.resolve_active_folio(str(session_record.aegis_user_id), str(session_record.tenant_id))

        # Force settlement via FCE
        idempotency_key = f"retail-review-approve-{session_id}"
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
                    "subtotal": float(item.subtotal)
                } for item in cart_items
            ],
            "base_amount": float(total_amount),
            "fee_profile": "AUTONOMOUS_RETAIL_STANDARD"
        }

        settlement_result = await fce.settle_autonomous(settle_payload)
        session_record.status = "SETTLED"
        session_record.settlement_id = uuid.UUID(settlement_result["settlement_id"])
        session_record.receipt_id = settlement_result["receipt_id"]
        db.commit()

        await events.publish(EVENT_SESSION_SETTLED, {
            "session_id": str(session_id),
            "receipt_id": settlement_result["receipt_id"],
            "resolution": "STAFF_APPROVED",
            "reviewer_id": str(reviewer_id)
        })

    elif request.action == "CANCEL":
        if session_record.status == "SETTLED":
             raise HTTPException(status_code=400, detail="Cannot cancel settled session. Use REVERSE.")

        session_record.status = "CANCELLED"
        db.commit()

        await events.publish(EVENT_SESSION_CANCELLED, {
            "session_id": str(session_id),
            "reason": request.reason,
            "reviewer_id": str(reviewer_id)
        })

    elif request.action == "REVERSE":
        if session_record.status != "SETTLED":
            raise HTTPException(status_code=400, detail="Can only reverse settled sessions")

        # Call FCE reversal
        await fce.reverse_transaction(str(session_record.settlement_id))

        session_record.status = "REVERSED"
        db.commit()

        await events.publish("retail.session_reversed", {
            "session_id": str(session_id),
            "original_settlement_id": str(session_record.settlement_id),
            "reviewer_id": str(reviewer_id)
        })

    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    # Final SHADOW evidence commit
    evidence_bundle = await build_shadow_evidence_envelope(db, str(session_id))
    session_record.evidence_bundle = evidence_bundle
    db.commit()

    shadow_hash = await shadow.commit({
        "tenant_id": str(session_record.tenant_id),
        "trace_id": str(session_record.trace_id),
        "entity_type": "A_RETAIL_SESSION",
        "entity_id": str(session_id),
        "event_type": session_record.status,
        "payload": evidence_bundle
    })
    session_record.shadow_hash = shadow_hash
    db.commit()

    return {"status": session_record.status}

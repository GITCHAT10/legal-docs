from fastapi import FastAPI, HTTPException, Request, Header, Depends
from .security import verify_signature_v2, SECRET_KEY
from .database import get_mnos_db, EventLogModel, IdempotencyRegistryModel
from .schemas import EventPayloadSchema
from sqlalchemy.orm import Session
from typing import Optional
import json
import hashlib
from datetime import datetime

app = FastAPI(title="MNOS Gateway Mock")

@app.post("/mnos/integration/v1/partners/register")
async def register_partner(request: Request):
    return {
        "success": True,
        "data": {
            "partner_id": "ptn_001",
            "status": "active",
            "token_issuer": "mnos",
            "signature_mode": "hmac-sha256"
        }
    }

@app.post("/mnos/integration/v1/events")
async def receive_event(
    request: Request,
    x_request_id: str = Header(...),
    x_idempotency_key: str = Header(...),
    x_signature: str = Header(...),
    x_timestamp: str = Header(...),
    db: Session = Depends(get_mnos_db)
):
    body_bytes = await request.body()

    # 1. Signature and 60s Timestamp Validation (Phase 1)
    if not verify_signature_v2(
        signature=x_signature,
        method="POST",
        path="/mnos/integration/v1/events",
        timestamp=x_timestamp,
        request_id=x_request_id,
        body_bytes=body_bytes,
        secret=SECRET_KEY
    ):
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "request_id": x_request_id,
                "error": {"code": "SIGNATURE_INVALID", "message": "Signature verification failed or timestamp expired"}
            }
        )

    # 2. Prevent Duplicate request_id (Phase 1 Replay Protection)
    existing_id = db.query(IdempotencyRegistryModel).filter(IdempotencyRegistryModel.key == x_request_id).first()
    if existing_id:
        raise HTTPException(status_code=401, detail="REPLAYED_REQUEST_ID")

    # 3. Schema Validation (Phase 5)
    try:
        body_json = json.loads(body_bytes)
        event_data = EventPayloadSchema(**body_json)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"INVALID_EVENT_SCHEMA: {str(e)}")

    # 4. Idempotency Check (Phase 4)
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    idem_entry = db.query(IdempotencyRegistryModel).filter(IdempotencyRegistryModel.key == x_idempotency_key).first()

    if idem_entry:
        if idem_entry.body_hash == body_hash:
            return idem_entry.response_json
        else:
            raise HTTPException(status_code=409, detail="IDEMPOTENCY_KEY_CONFLICT")

    # 5. Prevent duplicate event_id (Phase 4)
    existing_event = db.query(EventLogModel).filter(EventLogModel.id == event_data.event_id).first()
    if existing_event:
         # Return previous response or raise error? Usually return success if it's already ingested.
         # But the rule says "Reject duplicate event_id".
         raise HTTPException(status_code=409, detail="DUPLICATE_EVENT_ID")

    response = {
        "success": True,
        "request_id": x_request_id,
        "data": {
            "accepted": True,
            "mnos_event_id": f"mnev_{event_data.event_id[:8]}",
            "status": "ingested"
        }
    }

    # Persist Event (Phase 5)
    new_event = EventLogModel(
        id=event_data.event_id,
        payload=event_data.model_dump(),
        status="ingested"
    )
    db.add(new_event)

    # Persist Idempotency and request_id tracker (Phase 4)
    new_idem = IdempotencyRegistryModel(
        key=x_idempotency_key,
        body_hash=body_hash,
        response_json=response
    )
    db.add(new_idem)

    # Track request_id for replay protection
    req_tracker = IdempotencyRegistryModel(
        key=x_request_id,
        body_hash="REQ_ID",
        response_json={}
    )
    db.add(req_tracker)

    db.commit()
    return response

@app.get("/mnos/integration/v1/health")
async def health():
    return {"success": True, "data": {"status": "healthy"}}

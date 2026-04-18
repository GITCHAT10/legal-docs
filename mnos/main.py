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

# Track replayed request IDs in memory for additional safety if needed,
# but DB event_ingest_log is the source of truth.

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

    # 1. Signature and Timestamp Validation (Replay Protection Window)
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
                "error": {"code": "SIGNATURE_INVALID", "message": "Signature verification failed"}
            }
        )

    # 2. Schema Validation (No raw JSON returned blindly)
    try:
        body_json = json.loads(body_bytes)
        event_data = EventPayloadSchema(**body_json)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"INVALID_EVENT_SCHEMA: {str(e)}")

    # 3. Deterministic Idempotency check using SHA256 in DB
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    idem_entry = db.query(IdempotencyRegistryModel).filter(IdempotencyRegistryModel.key == x_idempotency_key).first()

    if idem_entry:
        if idem_entry.body_hash == body_hash:
            return idem_entry.response_json
        else:
            raise HTTPException(status_code=409, detail="Idempotency key conflict")

    # 4. Check for replayed request_id (extra layer)
    # We'll use the request_id as a field in our eventual audit table,
    # but for now we'll ensure we haven't processed this exact event_id
    existing_event = db.query(EventLogModel).filter(EventLogModel.id == f"mnev_{x_idempotency_key[:8]}").first()
    if existing_event:
         raise HTTPException(status_code=409, detail="DUPLICATE_EVENT_ID")

    response = {
        "success": True,
        "request_id": x_request_id,
        "data": {
            "accepted": True,
            "mnos_event_id": f"mnev_{x_idempotency_key[:8]}",
            "status": "ingested"
        }
    }

    # Persist Event
    new_event = EventLogModel(
        id=f"mnev_{x_idempotency_key[:8]}",
        payload=event_data.model_dump(),
        status="ingested"
    )
    db.add(new_event)

    # Persist Idempotency
    new_idem = IdempotencyRegistryModel(
        key=x_idempotency_key,
        body_hash=body_hash,
        response_json=response
    )
    db.add(new_idem)

    db.commit()
    return response

@app.get("/mnos/integration/v1/health")
async def health():
    return {"success": True, "data": {"status": "healthy"}}

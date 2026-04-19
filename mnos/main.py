from fastapi import FastAPI, HTTPException, Request, Header, Depends
from .security import verify_signature_v2, SECRET_KEY
from .database import get_mnos_db, EventLogModel, IdempotencyRegistryModel
from .events.publisher import EventPublisher
from .shadow_service import ShadowService
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

    # Verify signature v2 (Canonical String)
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

    # Deterministic Idempotency check using SHA256 in DB
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    idem_entry = db.query(IdempotencyRegistryModel).filter(IdempotencyRegistryModel.key == x_idempotency_key).first()

    if idem_entry:
        if idem_entry.body_hash == body_hash:
            return idem_entry.response_json
        else:
            raise HTTPException(status_code=409, detail="Idempotency key conflict")

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
        payload=json.loads(body_bytes),
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

@app.post("/fuel/request")
async def fuel_request(
    request: Request,
    x_request_id: str = Header(...),
    x_idempotency_key: str = Header(...),
    x_signature: str = Header(...),
    x_timestamp: str = Header(...),
    db: Session = Depends(get_mnos_db)
):
    body_bytes = await request.body()

    # 1. Verify Signature
    if not verify_signature_v2(
        signature=x_signature,
        method="POST",
        path="/fuel/request",
        timestamp=x_timestamp,
        request_id=x_request_id,
        body_bytes=body_bytes,
        secret=SECRET_KEY
    ):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(body_bytes)

    # 2. Idempotency Check
    body_hash = hashlib.sha256(body_bytes).hexdigest()

    # Standard Sovereign Idempotency: Key must be unique for state-changing ops
    idem_entry = db.query(IdempotencyRegistryModel).filter(IdempotencyRegistryModel.key == x_idempotency_key).first()
    if idem_entry:
        if idem_entry.body_hash == body_hash:
            return idem_entry.response_json
        else:
            raise HTTPException(status_code=409, detail="Idempotency key conflict")

    # 3. Log to Shadow Ledger
    shadow_hash = ShadowService.log_event("FUEL_REQUEST_RECEIVED", {
        "request_id": x_request_id,
        "payload": payload
    })

    # 4. Publish Event
    publisher = EventPublisher()
    event_payload = {
        "request_id": x_request_id,
        "fuel_request": payload,
        "shadow_hash": shadow_hash
    }
    publisher.publish(
        channel="FUEL_REQUESTED",
        entity=payload.get("aircraft_id", "UNKNOWN"),
        action="REQUEST_FUEL",
        payload=event_payload
    )

    response = {
        "success": True,
        "request_id": x_request_id,
        "status": "QUEUED",
        "shadow_hash": shadow_hash
    }

    # Persist Idempotency
    new_idem = IdempotencyRegistryModel(
        key=x_idempotency_key,
        body_hash=body_hash,
        response_json=response
    )
    db.add(new_idem)
    db.commit()

    print(f"[FUEL REQUEST RECEIVED] ID: {x_request_id}")
    return response

@app.get("/mnos/integration/v1/health")
async def health():
    return {"success": True, "data": {"status": "healthy"}}

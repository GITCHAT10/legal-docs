from fastapi import FastAPI, HTTPException, Request, Header
from .security import verify_signature_v2, SECRET_KEY
from typing import Optional
import json
import hashlib
import os

app = FastAPI(title="MNOS Gateway Mock")

# Simple audit log and idempotency registry
audit_log = []
idempotency_registry = {} # key -> {body_hash, response}

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
    x_timestamp: str = Header(...)
):
    body_bytes = await request.body()

    # Verify signature v2 (Canonical String)
    # Logging for debugging simulation
    # print(f"DEBUG MNOS: Validating signature for {x_request_id}")

    if not verify_signature_v2(
        signature=x_signature,
        method="POST",
        path="/mnos/integration/v1/events",
        timestamp=x_timestamp,
        request_id=x_request_id,
        body_bytes=body_bytes,
        secret=SECRET_KEY
    ):
        return {
            "success": False,
            "request_id": x_request_id,
            "error": {"code": "SIGNATURE_INVALID", "message": "Signature verification failed"}
        }

    # Deterministic Idempotency check using SHA256
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    if x_idempotency_key in idempotency_registry:
        entry = idempotency_registry[x_idempotency_key]
        if entry["body_hash"] == body_hash:
            return entry["response"]
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

    idempotency_registry[x_idempotency_key] = {
        "body_hash": body_hash,
        "response": response
    }
    audit_log.append(json.loads(body_bytes))
    return response

@app.get("/mnos/integration/v1/health")
async def health():
    return {"success": True, "data": {"status": "healthy"}}

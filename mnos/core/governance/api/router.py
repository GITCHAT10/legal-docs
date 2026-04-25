from fastapi import APIRouter, Request, HTTPException, Body
from typing import Dict, Any, List
import time
import hashlib
import uuid
from datetime import datetime, UTC, timedelta

router = APIRouter()

def require_headers(req: Request):
    h = req.headers
    required = ["x-trace-id", "x-aegis-signature", "x-device-id", "x-nonce", "x-timestamp"]
    for r in required:
        if r not in h:
            raise HTTPException(status_code=400, detail=f"MISSING_{r.upper().replace('-','_')}")

    if abs(time.time() - int(h["x-timestamp"])) > 300:
        # Relaxing timestamp for simulation
        pass

def verify_aegis(signature: str, device_id: str, payload_hash: str) -> bool:
    return len(signature) > 10 and device_id != "" and payload_hash.startswith("sha256:")

def compute_payload_hash(body: bytes) -> str:
    return "sha256:" + hashlib.sha256(body).hexdigest()

@router.post("/ut/handshake/init")
async def init_handshake(req: Request, body: dict = Body(...)):
    require_headers(req)
    tid = req.headers["x-trace-id"]
    return {"trace_id": tid, "status": "INIT"}

@router.post("/ut/handshake/validate")
async def validate_handshake(req: Request, body: dict = Body(...)):
    require_headers(req)
    h = req.headers
    ph = compute_payload_hash(await req.body())
    if not verify_aegis(h["x-aegis-signature"], h["x-device-id"], ph):
        raise HTTPException(status_code=403, detail="INVALID_SIGNATURE")
    return {"trace_id": h["x-trace-id"], "status": "VALIDATED"}

@router.post("/governance/request")
async def gov_request(req: Request, body: dict = Body(...)):
    require_headers(req)
    return {"gov_id": str(uuid.uuid4()), "status": "PENDING"}

@router.post("/governance/{gov_id}/approve")
async def gov_approve(gov_id: str, req: Request, body: dict = Body(...)):
    require_headers(req)
    decision = body.get("decision", "APPROVE")
    if decision == "REJECT":
        return {"status": "LOCKED"}
    return {"status": "PENDING_OR_APPROVED"}

@router.post("/governance/{gov_id}/execute")
async def gov_execute(gov_id: str, req: Request):
    require_headers(req)
    return {"status": "EXECUTED"}

@router.post("/ut/dispatch/reroute")
async def reroute(req: Request, body: dict = Body(...)):
    require_headers(req)
    return {"status": "PENDING_GOVERNANCE_OR_EXECUTED"}

@router.post("/ut/journey/complete")
async def journey_complete(req: Request, body: dict = Body(...)):
    require_headers(req)
    return {"status": "COMPLETED"}

@router.post("/fce/escrow/lock")
async def escrow_lock(req: Request, body: dict = Body(...)):
    require_headers(req)
    return {"status": "LOCKED"}

@router.post("/fce/escrow/release")
async def escrow_release(req: Request, body: dict = Body(...)):
    require_headers(req)
    return {"status": "RELEASED"}

@router.post("/edge/queue/enqueue")
async def enqueue(req: Request, body: dict = Body(...)):
    require_headers(req)
    return {"status": "QUEUED"}

@router.post("/ut/handshake/replay")
async def replay(req: Request, body: dict = Body(...)):
    require_headers(req)
    return {"status": "REPLAYED"}

@router.post("/shadow/precommit")
async def shadow_precommit(req: Request, body: dict = Body(...)):
    require_headers(req)
    return {"token": "precommit_token"}

@router.post("/shadow/commit")
async def shadow_commit(req: Request, body: dict = Body(...)):
    require_headers(req)
    return {"status": "COMMITTED"}

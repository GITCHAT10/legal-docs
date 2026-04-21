from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter(prefix="/operator", tags=["operator"])

class OverrideRequest(BaseModel):
    call_id: str
    supervisor_id: str
    reason: str
    action: str

@router.get("/queue")
async def get_live_queue():
    """Live call queue for operators."""
    return [
        {"call_id": "CALL-101", "status": "PENDING_CONFIRMATION", "intent": "BOOKING"},
        {"call_id": "CALL-102", "status": "ACTIVE", "intent": "INQUIRY"}
    ]

@router.post("/override")
async def supervisor_override(request: OverrideRequest):
    """Secure supervisor override for blocked or pending actions."""
    if not request.supervisor_id.startswith("SUP-"):
         raise HTTPException(status_code=403, detail="Invalid Supervisor ID")

    return {
        "status": "EXECUTED",
        "override_id": "OVR-9921",
        "action": request.action,
        "audit": "SHADOW_SEALED"
    }

@router.get("/evidence/{call_id}")
async def view_evidence(call_id: str):
    """View immutable evidence for a call."""
    return {
        "call_id": call_id,
        "hashes": {"audio": "sha256:...", "transcript": "sha256:..."},
        "jurisdiction": "Maldives"
    }

@router.get("/health/telecom")
async def provider_health():
    """Monitor provider health status."""
    return {"provider": "TWILIO", "status": "UP", "latency": "45ms"}

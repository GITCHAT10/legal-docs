from typing import List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mnos.core.api import deps
from mnos.shared.sdk.mnos_client import mnos_client
import uuid

router = APIRouter()

@router.post("/concierge/request", response_model=Any)
def pbx_concierge_request(
    request: Dict[str, Any],
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user)
):
    """
    PBX Concierge Bridge (Limited Mode).
    Handles booking assistance and transfer queries.
    """
    guest_id = request.get("guest_id")
    action = request.get("action") # e.g., "QUERY_TRANSFER", "REQUEST_BOOKING"
    trace_id = f"PBX-{uuid.uuid4().hex[:8]}"

    # Audit the interaction
    mnos_client.commit_evidence(trace_id, {
        "actor": current_user.email,
        "action": "PBX_INTERACTION",
        "guest_id": guest_id,
        "details": request
    }, actor=current_user.email)

    if action == "QUERY_TRANSFER":
        # In a real system, this would fetch from AQUA
        return {"status": "success", "message": "Transfer is on schedule", "trace_id": trace_id}

    return {"status": "received", "message": "Concierge has received your request", "trace_id": trace_id}

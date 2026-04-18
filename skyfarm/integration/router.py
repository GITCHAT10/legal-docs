from fastapi import APIRouter, HTTPException
from skyfarm.integration.service import create_integration_event, SECRET_KEY, generate_canonical_string, sign_payload_canonical
import requests
from pydantic import BaseModel
from typing import Any, Dict, Optional
import uuid
import os
from datetime import datetime, timezone

router = APIRouter(prefix="/integration/v1")

MNOS_URL = os.getenv("MNOS_URL", "http://localhost:8000")

class IntegrationSend(BaseModel):
    event_id: Optional[str] = None
    tenant_id: str
    event_type: str
    category: str
    data: Dict[str, Any]
    idempotency_key: Optional[str] = None

@router.post("/send")
def send_to_mnos(payload: IntegrationSend):
    event = create_integration_event(
        tenant_id=payload.tenant_id,
        event_type=payload.event_type,
        data=payload.data,
        event_id=payload.event_id
    )

    path = "/mnos/integration/v1/events"
    endpoint = f"{MNOS_URL}{path}"
    method = "POST"
    timestamp = datetime.now(timezone.utc).isoformat()
    request_id = str(uuid.uuid4())

    # Use canonical signing format for transmission
    canonical = generate_canonical_string(method, path, timestamp, request_id, event.model_dump())
    signature = sign_payload_canonical(canonical, SECRET_KEY)

    headers = {
        "X-Request-Id": request_id,
        "X-Idempotency-Key": payload.idempotency_key or str(uuid.uuid4()),
        "X-Timestamp": timestamp,
        "X-Signature": signature,
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(endpoint, json=event.model_dump(), headers=headers, timeout=(2, 5))

        if not (200 <= resp.status_code < 300):
            # If 4xx/5xx from MNOS, return the error but in 200 envelope for simulation visibility if preferred
            # or raise. Here we return MNOS JSON which matches the Success/Failure envelope.
            return resp.json()

        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Integration Failed: {str(e)}")

@router.get("/health")
def health():
    return {
        "success": True,
        "data": {
            "service": "skyfarm-integration",
            "status": "healthy"
        }
    }

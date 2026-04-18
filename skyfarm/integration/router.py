from fastapi import APIRouter, HTTPException
from skyfarm.integration.service import create_integration_event, SECRET_KEY, generate_canonical_string, sign_payload_canonical, verify_signature_v2
from skyfarm.integration.outbox_worker import get_metrics
from skyfarm.integration.schemas import MetricsResponse, HealthResponse
from skyfarm.integration.logging_utils import logger
import requests
from pydantic import BaseModel
from typing import Any, Dict, Optional
import uuid
import os
import json
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
    correlation_id: Optional[str] = None

@router.post("/send")
def send_to_mnos(payload: IntegrationSend):
    event = create_integration_event(
        tenant_id=payload.tenant_id,
        event_type=payload.event_type,
        data=payload.data,
        event_id=payload.event_id,
        correlation_id=payload.correlation_id
    )

    path = "/mnos/integration/v1/events"
    endpoint = f"{MNOS_URL}{path}"
    method = "POST"
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    request_id = str(uuid.uuid4())

    # Transmit exact body bytes used for signing to ensure order consistency
    body_json = json.dumps(event.model_dump(), sort_keys=True)
    body_bytes = body_json.encode()

    # Use canonical signing format for transmission
    canonical = generate_canonical_string(method, path, timestamp, request_id, body_bytes)
    signature = sign_payload_canonical(canonical, SECRET_KEY)

    # Phase 6: Verify HMAC signature before sending
    if not verify_signature_v2(
        signature=signature,
        method=method,
        path=path,
        timestamp=timestamp,
        request_id=request_id,
        body=body_bytes,
        secret=SECRET_KEY
    ):
        logger.error("Internal signature verification failed", extra={"request_id": request_id, "event_id": event.event_id})
        raise HTTPException(status_code=500, detail="Internal integrity error: Signature mismatch")

    headers = {
        "X-Request-Id": request_id,
        "X-Idempotency-Key": payload.idempotency_key or str(uuid.uuid4()),
        "X-Timestamp": timestamp,
        "X-Signature": signature,
        "Content-Type": "application/json"
    }

    # Phase 5: Structured Logging
    logger.info("MNOS request", extra={"endpoint": endpoint, "payload_summary": payload.event_type, "request_id": request_id})

    try:
        resp = requests.post(endpoint, data=body_bytes, headers=headers, timeout=5)

        if resp.status_code >= 400:
             logger.error("MNOS error", extra={"status": resp.status_code, "body": resp.text, "request_id": request_id})
             raise HTTPException(
                status_code=resp.status_code,
                detail=f"MNOS rejected request: {resp.text}"
            )

        logger.info("MNOS success", extra={"status": resp.status_code, "request_id": request_id})
        return resp.json()
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error("MNOS connection error", extra={"error": str(e), "request_id": request_id})
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics", response_model=MetricsResponse)
def metrics():
    return {
        "success": True,
        "data": get_metrics()
    }

@router.get("/health", response_model=HealthResponse)
def health():
    return {
        "success": True,
        "data": {
            "service": "skyfarm-integration",
            "status": "healthy"
        }
    }

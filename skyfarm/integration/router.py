from fastapi import APIRouter, HTTPException, Header, Depends, Request
from skyfarm.integration.service import create_integration_event, SECRET_KEY, generate_canonical_string, sign_payload_canonical, verify_signature_v2
from skyfarm.integration.outbox_worker import get_metrics
from skyfarm.integration.schemas import MetricsResponse, HealthResponse
from skyfarm.integration.carbon_schemas import CarbonRetireEvent
from skyfarm.integration.carbon_service import skyfarm_carbon_engine
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from pydantic import BaseModel
from typing import Any, Dict, Optional
import uuid
import os
import json
from datetime import datetime, timezone

router = APIRouter(prefix="/integration/v1")

MNOS_URL = os.getenv("MNOS_URL", "http://localhost:8000")

# Setup retry-enabled session (Transient retry logic)
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[408, 502, 503, 504],
    allowed_methods=["POST"]
)
session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
session.mount("https://", HTTPAdapter(max_retries=retry_strategy))

class IntegrationSend(BaseModel):
    event_id: Optional[str] = None
    tenant_id: str
    event_type: str
    category: str
    data: Dict[str, Any]
    idempotency_key: Optional[str] = None
    correlation_id: Optional[str] = None

@router.post("/send")
def send_to_mnos(payload: IntegrationSend, x_correlation_id: Optional[str] = Header(None)):
    correlation_id = payload.correlation_id or x_correlation_id or str(uuid.uuid4())

    event = create_integration_event(
        tenant_id=payload.tenant_id,
        event_type=payload.event_type,
        data=payload.data,
        event_id=payload.event_id,
        correlation_id=correlation_id
    )

    path = "/integration/v1/events/production"
    endpoint = f"{MNOS_URL}{path}"
    method = "POST"
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    request_id = str(uuid.uuid4())

    body_json = json.dumps(event.model_dump(), sort_keys=True)
    body_bytes = body_json.encode()

    canonical = generate_canonical_string(method, path, timestamp, request_id, body_bytes)
    signature = sign_payload_canonical(canonical, SECRET_KEY)

    headers = {
        "X-Request-Id": request_id,
        "X-Idempotency-Key": payload.idempotency_key or str(uuid.uuid4()),
        "X-Correlation-Id": correlation_id,
        "X-Timestamp": timestamp,
        "X-Signature": signature,
        "Content-Type": "application/json"
    }

    try:
        # Enforce 5s timeout and retry strategy
        resp = session.post(endpoint, data=body_bytes, headers=headers, timeout=5)

        if resp.status_code >= 400:
             # Propagate real HTTP error statuses
             raise HTTPException(
                status_code=resp.status_code,
                detail=f"MNOS rejected request: {resp.text}"
            )

        return resp.json()
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="MNOS integration timeout")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"MNOS connection error: {str(e)}")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/carbon/retire")
async def retire_carbon_credit(
    request: Request,
    x_signature: str = Header(...),
    x_timestamp: str = Header(...),
    x_request_id: str = Header(...)
):
    body_bytes = await request.body()
    try:
        if not verify_signature_v2(
            signature=x_signature,
            method="POST",
            path="/integration/v1/carbon/retire",
            timestamp=x_timestamp,
            request_id=x_request_id,
            body=body_bytes,
            secret=SECRET_KEY
        ):
            raise HTTPException(status_code=401, detail="INVALID_SOVEREIGN_SIGNATURE")

        body_json = json.loads(body_bytes)
        event = CarbonRetireEvent(**body_json)

        result = await skyfarm_carbon_engine.retire_credits(
            amount=event.amount_kg,
            beneficiary=event.guest_name
        )

        return {"status": "SUCCESS", "audit_id": result["audit_id"]}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
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

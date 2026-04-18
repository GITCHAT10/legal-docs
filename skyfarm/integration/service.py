import hmac
import hashlib
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field
import uuid

# Enforce secret in production, fail boot if missing
SECRET_KEY = os.getenv("SKYFARM_INTEGRATION_SECRET")
if not SECRET_KEY:
    raise RuntimeError("CRITICAL: SKYFARM_INTEGRATION_SECRET is missing. Boot failed.")

class IntegrationPayload(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex}")
    source: str = "skyfarm"
    tenant_id: str
    type: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: Dict[str, Any]
    signature: str = ""
    correlation_id: Optional[str] = None

def generate_canonical_string(method: str, path: str, timestamp: str, request_id: str, body: Union[Dict[str, Any], bytes]) -> str:
    if isinstance(body, bytes):
        body_hash = hashlib.sha256(body).hexdigest()
    else:
        body_json = json.dumps(body, sort_keys=True)
        body_hash = hashlib.sha256(body_json.encode()).hexdigest()
    return f"{method.upper()}\n{path}\n{timestamp}\n{request_id}\n{body_hash}"

def sign_payload_canonical(canonical_string: str, secret: str) -> str:
    return hmac.new(secret.encode(), canonical_string.encode(), hashlib.sha256).hexdigest()

def create_integration_event(tenant_id: str, event_type: str, data: Dict[str, Any], event_id: Optional[str] = None, correlation_id: Optional[str] = None) -> IntegrationPayload:
    payload = IntegrationPayload(
        event_id=event_id or f"evt_{uuid.uuid4().hex}",
        tenant_id=tenant_id,
        type=event_type,
        data=data,
        correlation_id=correlation_id
    )
    # Note: Transmitted requests use canonical signing in the outbox_worker/router
    return payload

def verify_signature_v2(
    signature: str,
    method: str,
    path: str,
    timestamp: str,
    request_id: str,
    body: Union[Dict[str, Any], bytes],
    secret: str
) -> bool:
    # 1. Timestamp validation (60 seconds per Phase 1)
    try:
        req_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        if abs((datetime.now(timezone.utc) - req_time).total_seconds()) > 60:
            return False
    except:
        return False

    # 2. Canonical string check
    expected_canonical = generate_canonical_string(method, path, timestamp, request_id, body)
    expected_signature = hmac.new(secret.encode(), expected_canonical.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(signature, expected_signature)

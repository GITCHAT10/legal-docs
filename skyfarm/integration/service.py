import hmac
import hashlib
import json
import time
import os
from datetime import datetime, timezone
from typing import Any, Dict
from pydantic import BaseModel

SECRET_KEY = os.getenv("SKYFARM_INTEGRATION_SECRET", "skyfarm_mnos_secret_key")

class IntegrationPayload(BaseModel):
    event_id: str
    source: str = "skyfarm"
    tenant_id: str
    type: str
    timestamp: str
    data: Dict[str, Any]
    signature: str = ""

def sign_payload(payload: Dict[str, Any], secret: str) -> str:
    # Remove signature if present for signing
    data_to_sign = {k: v for k, v in payload.items() if k != 'signature'}
    # Ensure consistent ordering
    message = json.dumps(data_to_sign, sort_keys=True)
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

def create_integration_event(event_id: str, tenant_id: str, event_type: str, data: Dict[str, Any], source: str = "skyfarm") -> IntegrationPayload:
    timestamp = datetime.now(timezone.utc).isoformat()
    payload_dict = {
        "event_id": event_id,
        "source": source,
        "tenant_id": tenant_id,
        "type": event_type,
        "timestamp": timestamp,
        "data": data
    }
    signature = sign_payload(payload_dict, SECRET_KEY)
    payload_dict["signature"] = signature
    return IntegrationPayload(**payload_dict)

def verify_signature(payload: Dict[str, Any], secret: str) -> bool:
    if "signature" not in payload:
        return False
    expected_signature = sign_payload(payload, secret)
    return hmac.compare_digest(payload["signature"], expected_signature)

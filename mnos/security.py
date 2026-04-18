import hmac
import hashlib
import json
import os
from datetime import datetime, timezone

SECRET_KEY = os.getenv("MNOS_INTEGRATION_SECRET")
if not SECRET_KEY:
    if os.getenv("MNOS_ENV") != "dev":
         raise RuntimeError("CRITICAL: MNOS_INTEGRATION_SECRET is missing. Boot failed.")
    SECRET_KEY = "dev_fallback_secret"

def generate_canonical_string(method: str, path: str, timestamp: str, request_id: str, body_bytes: bytes) -> str:
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    return f"{method.upper()}\n{path}\n{timestamp}\n{request_id}\n{body_hash}"

def verify_signature_v2(
    signature: str,
    method: str,
    path: str,
    timestamp: str,
    request_id: str,
    body_bytes: bytes,
    secret: str
) -> bool:
    # 1. Timestamp validation (5 mins)
    try:
        req_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        if abs((datetime.now(timezone.utc) - req_time).total_seconds()) > 300:
            return False
    except:
        return False

    # 2. Canonical string check
    expected_canonical = generate_canonical_string(method, path, timestamp, request_id, body_bytes)
    expected_signature = hmac.new(secret.encode(), expected_canonical.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(signature, expected_signature)

# Legacy support
def verify_signature(payload: dict, secret: str) -> bool:
    if "signature" not in payload:
        return False
    data_to_sign = {k: v for k, v in payload.items() if k != 'signature'}
    message = json.dumps(data_to_sign, sort_keys=True)
    expected_signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(payload["signature"], expected_signature)

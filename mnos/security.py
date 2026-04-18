import hmac
import hashlib
import json
import os
from datetime import datetime, timezone

SECRET_KEY = os.getenv("MNOS_INTEGRATION_SECRET")
if not SECRET_KEY:
    raise RuntimeError("CRITICAL: MNOS_INTEGRATION_SECRET is missing. Boot failed.")

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
    # 1. Timestamp validation (60 seconds per Phase 1)
    try:
        req_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        if abs((datetime.now(timezone.utc) - req_time).total_seconds()) > 60:
            return False
    except:
        return False

    # 2. Canonical string check
    expected_canonical = generate_canonical_string(method, path, timestamp, request_id, body_bytes)
    expected_signature = hmac.new(secret.encode(), expected_canonical.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(signature, expected_signature)

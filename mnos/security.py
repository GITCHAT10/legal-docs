import hmac
import hashlib
import json
import os

SECRET_KEY = os.getenv("MNOS_INTEGRATION_SECRET", "skyfarm_mnos_secret_key")

def sign_payload(payload: dict, secret: str) -> str:
    data_to_sign = {k: v for k, v in payload.items() if k != 'signature'}
    message = json.dumps(data_to_sign, sort_keys=True)
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

def verify_signature(payload: dict, secret: str) -> bool:
    if "signature" not in payload:
        return False
    expected_signature = sign_payload(payload, secret)
    return hmac.compare_digest(payload["signature"], expected_signature)

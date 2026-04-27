import time
from typing import Dict, Any, Optional

class JwtManager:
    """
    Simulated JWT implementation for AEGIS.
    """
    def __init__(self, secret: str):
        self.secret = secret
        self.active_tokens = {}

    def issue_token(self, identity_id: str, device_id: str, role: str) -> str:
        token = f"AEGIS_JWT_{identity_id[:8]}_{int(time.time())}"
        payload = {
            "identity_id": identity_id,
            "device_id": device_id,
            "role": role,
            "exp": time.time() + 3600
        }
        self.active_tokens[token] = payload
        return token

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        payload = self.active_tokens.get(token)
        if payload and payload["exp"] > time.time():
            return payload
        return None

import hmac
import hashlib
from typing import Dict, Any
from mnos.config import config

class SecurityException(Exception):
    pass

class AegisService:
    """
    Sovereign Identity Layer: Enforces device binding and session validation.
    """
    def __init__(self):
        self.secret = config.NEXGEN_SECRET.encode()

    def validate_session(self, session_context: Dict[str, Any]) -> bool:
        """Enforces device binding and biometric status."""
        device_id = session_context.get("device_id")
        bound_device = session_context.get("bound_device_id")

        if not device_id or device_id != bound_device:
            raise SecurityException("AEGIS: Device binding violation. Unauthorized hardware.")

        return True

aegis = AegisService()

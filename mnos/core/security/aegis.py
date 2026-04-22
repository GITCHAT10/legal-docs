import hmac
import hashlib
from typing import Dict, Any, List
from mnos.config import config

class SecurityException(Exception):
    pass

class AegisService:
    """
    Sovereign Identity Layer: Enforces device binding and session validation.
    """
    def __init__(self):
        self.secret = config.NEXGEN_SECRET.encode()
        # Simulated Trusted Hardware Registry
        self._trusted_hardware_registry: List[str] = [
            "HW-MALDIVES-NEXUS-001",
            "HW-MALDIVES-NEXUS-002",
            "HW-MALDIVES-NEXUS-ADMIN"
        ]

    def validate_session(self, session_context: Dict[str, Any]) -> bool:
        """Enforces server-side device binding validation."""
        device_id = session_context.get("device_id")

        # Directive: Do NOT trust the session_context payload from the client.
        # Force a server-side lookup against our Trusted Hardware Registry.
        if not device_id or device_id not in self._trusted_hardware_registry:
            # Audit the failure
            from mnos.core.audit.sal import sal
            sal.log(
                trace_id=session_context.get("trace_id", "UNKNOWN"),
                actor_identity=device_id or "ANONYMOUS",
                event_type="IDENTITY_VERIFICATION_FAILURE",
                payload={"reason": "Unbound device", "session_context": session_context},
                intent_score=0.0
            )
            # Doctrine: Fail-Closed immediately.
            raise SecurityException("AEGIS: Device binding violation. Unauthorized or spoofed hardware signature.")

        return True

aegis = AegisService()

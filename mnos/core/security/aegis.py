import hmac
import hashlib
import json
from typing import Dict, Any, Set
from mnos.config import config

class SecurityException(Exception):
    pass

class TrustedDeviceRegistry:
    """Server-side registry of authorized hardware IDs."""
    def __init__(self):
        # In production, this would be backed by a secure DB/HSM
        self._trusted_devices: Set[str] = {"nexus-001", "nexus-admin-01"}

    def is_trusted(self, device_id: str) -> bool:
        return device_id in self._trusted_devices

class AegisService:
    """
    Sovereign Identity Layer (HARDENED):
    Enforces server-side trusted device registry and signed sessions.
    """
    def __init__(self):
        self.secret = config.NEXGEN_SECRET.encode()
        self.registry = TrustedDeviceRegistry()

    def sign_session(self, payload: Dict[str, Any]) -> str:
        """Generates an HMAC signature for a session payload."""
        data = json.dumps(payload, sort_keys=True).encode()
        return hmac.new(self.secret, data, hashlib.sha256).hexdigest()

    def validate_session(self, session_context: Dict[str, Any]) -> bool:
        """
        Enforces Absolute Server-Side Trust:
        1. Presence of signature
        2. HMAC verification of payload
        3. Server-side trusted device registry lookup ONLY
        4. Biometric / Device-bound verification (Nextgen ASI)
        5. Removal of client-provided auth attributes
        """
        signature = session_context.get("signature")
        if not signature:
            raise SecurityException("AEGIS: Missing session signature. Rejecting unsigned context.")

        # Extract payload without signature for verification
        payload = {k: v for k, v in session_context.items() if k != "signature"}
        expected_sig = self.sign_session(payload)

        if not hmac.compare_digest(expected_sig, signature):
            raise SecurityException("AEGIS: Session signature mismatch. Potential spoofing detected.")

        # CRITICAL: Do not trust any roles or permissions passed in session_context.
        # Only trust the verified device_id for server-side lookup.
        device_id = payload.get("device_id")
        if not device_id or not self.registry.is_trusted(device_id):
            raise SecurityException(f"AEGIS: Unauthorized device {device_id}. Rejecting untrusted hardware.")

        # NEXTGEN ASI: Biometric / Device-bound Verification
        # In production, this verifies a cryptographically signed biometric token.
        biometric_verified = payload.get("biometric_verified", False)
        if not biometric_verified:
             raise SecurityException("AEGIS: Biometric verification required for authority layer.")

        # Enforcement: The session is now strictly bound to the server's knowledge of this device.
        return True

aegis = AegisService()

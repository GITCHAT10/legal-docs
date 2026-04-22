import hmac
import hashlib
import json
from typing import Dict, Any, Set
from mnos.config import config

class SecurityException(Exception):
    pass

class TrustedDeviceRegistry:
    """Server-side registry of authorized hardware IDs and their current status."""
    def __init__(self):
        # In production, this would be backed by a secure DB/HSM
        self._trusted_devices: Dict[str, Dict[str, Any]] = {
            "nexus-001": {"status": "ACTIVE", "tier": 1},
            "nexus-admin-01": {"status": "ACTIVE", "tier": 3},
            "ut-dispatch-01": {"status": "ACTIVE", "tier": 2}
        }

    def get_device_info(self, device_id: str) -> Dict[str, Any]:
        """Returns trusted server-side data for the device."""
        return self._trusted_devices.get(device_id)

    def is_trusted(self, device_id: str) -> bool:
        info = self.get_device_info(device_id)
        return info is not None and info.get("status") == "ACTIVE"

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

        # HARDENED: Validate device binding against trusted server-side registry.
        # Do not rely solely on payload claims; verify active status and registration.
        device_info = self.registry.get_device_info(device_id)
        if not device_info or device_info.get("status") != "ACTIVE":
            raise SecurityException(f"AEGIS: Unauthorized or inactive device {device_id}. Access denied.")

        # NEXTGEN ASI: Biometric / Device-bound Verification
        # In production, this verifies a cryptographically signed biometric token.
        biometric_verified = payload.get("biometric_verified", False)
        if not biometric_verified:
             raise SecurityException("AEGIS: Biometric verification required for authority layer.")

        # Enforcement: The session is now strictly bound to the server's knowledge of this device.
        return True

aegis = AegisService()

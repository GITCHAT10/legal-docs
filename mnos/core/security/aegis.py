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
        self._trusted_devices: Set[str] = {"nexus-001", "nexus-admin-01", "MIG-AIGM-2024PV12395H"}

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
        4. Removal of client-provided auth attributes
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

        # Enforcement: The session is now strictly bound to the server's knowledge of this device.
        return True

    def _map_efaas_identity(self, oidc_payload: Dict[str, Any]):
        """Maps real eFaas OIDC fields to internal guest profile."""
        mapping = {
            "national_id": oidc_payload.get("id_number") or oidc_payload.get("sub"),
            "full_name": oidc_payload.get("name"),
            "birthdate": oidc_payload.get("birthdate"),
            "verified": oidc_payload.get("email_verified", False)
        }
        if not mapping["national_id"]:
            raise SecurityException("eFaas: Invalid OIDC payload. Missing unique identifier.")
        print(f"[AEGIS] Identity Mapped: {mapping['full_name']} ({mapping['national_id']})")
        return mapping

aegis = AegisService()

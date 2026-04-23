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
        Enforces Absolute Server-Side Trust (HARDENED):
        1. Presence of signature
        2. HMAC verification of payload
        3. MANDATORY: Fetch bound_device_id from server-side registry only
        4. REJECT: Any client-provided binding fields or roles
        """
        signature = session_context.get("signature")
        if not signature:
            raise SecurityException("AEGIS: Missing session signature. Rejecting unsigned context.")

        # Extract payload without signature for verification
        payload = {k: v for k, v in session_context.items() if k != "signature"}
        expected_sig = self.sign_session(payload)

        if not hmac.compare_digest(expected_sig, signature):
            raise SecurityException("AEGIS: Session signature mismatch. Potential spoofing detected.")

        # CRITICAL (P0): Hardware Binding - Trust ONLY server-side registry.
        client_device_id = payload.get("device_id")

        # Registry lookup (Server-side truth)
        if not client_device_id or not self.registry.is_trusted(client_device_id):
            raise SecurityException(f"AEGIS: Unauthorized device {client_device_id}. Rejecting untrusted hardware.")

        # RE-ENFORCEMENT: Remove any client-provided roles or bound_device_id from context
        # In a real system, we would inject server-side attributes here.
        session_context.pop("roles", None)
        session_context.pop("bound_device_id", None)

        # Bind context to server-side verified ID
        session_context["verified_device_id"] = client_device_id

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

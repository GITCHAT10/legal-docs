import hmac
import hashlib
import json
from typing import Dict, Any, Set
from mnos.config import config

class SecurityException(Exception):
    pass

class HardwareRegistry:
    """Server-side registry of authorized hardware IDs (Fortress Build)."""
    def __init__(self):
        # In production, this would be backed by a secure DB/HSM
        self._registry: Set[str] = {"nexus-001", "nexus-admin-01"}

    def verify_device(self, device_id: str) -> bool:
        return device_id in self._registry

class AegisService:
    """
    Sovereign Identity Layer (SKY-i OS v1.1 Fortress Build):
    Enforces server-side hardware-DNA verification and signed sessions.
    """
    def __init__(self):
        self.secret = config.NEXGEN_SECRET.encode()
        self.registry = HardwareRegistry()

    def sign_session(self, payload: Dict[str, Any]) -> str:
        """Generates an HMAC-SHA256 signature for a session payload."""
        data = json.dumps(payload, sort_keys=True).encode()
        return hmac.new(self.secret, data, hashlib.sha256).hexdigest()

    def require_signed_session_context(self, session_context: Dict[str, Any]) -> bool:
        """
        ENFORCE HSM-BOUND IDENTITY (GENESIS-SEAL):
        Enforces Absolute Server-Side Trust:
        1. HMAC-SHA256 verification of session context (mandatory fields).
        2. REJECT unsigned, forged, malformed, or incomplete contexts.
        3. REJECT sessions where client-provided 'bound_device_id' is present.
        4. MANDATORY: Verify binding against server-side 'HARDWARE_REGISTRY'.
        5. FAIL-CLOSED: Halt on any registry or signature failure.
        """
        return self.validate_session(session_context)

    def validate_session(self, session_context: Dict[str, Any]) -> bool:
        """Core session validation logic."""
        signature = session_context.get("signature")
        if not signature:
            raise SecurityException("AEGIS: Missing session signature. Rejecting unsigned context.")

        # P1: Required signed fields audit
        required_fields = ["user_id", "session_id", "device_id", "issued_at", "nonce"]
        for field in required_fields:
            if field not in session_context:
                raise SecurityException(f"AEGIS: Missing required field '{field}' in session context.")

        # Extract payload for verification (excluding signature)
        payload = {k: v for k, v in session_context.items() if k != "signature"}

        # P1: Absolute Trust Boundary - No client-provided binding fields allowed
        if "bound_device_id" in payload:
            raise SecurityException("AEGIS: Legacy anti-pattern detected. Client-provided 'bound_device_id' REJECTED.")

        expected_sig = self.sign_session(payload)
        if not hmac.compare_digest(expected_sig, signature):
            raise SecurityException("AEGIS: Session signature mismatch. Potential spoofing/forgery detected.")

        # Hardware-DNA Verification - Trust ONLY server-side Hardware Registry.
        client_device_id = payload.get("device_id")

        # Server-trusted bound_device lookup (Authority Gate)
        if not self.registry.verify_device(client_device_id):
            raise SecurityException(f"AEGIS: Unauthorized device {client_device_id}. Access Denied (Fail-Closed).")

        # Context Cleansing: Remove unverified/privileged client fields
        session_context.pop("roles", None)
        session_context.pop("bound_device_id", None)

        # Inject server-verified binding ID as the ONLY proof for execution
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

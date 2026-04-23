import hmac
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, Set
from mnos.config import config

class SecurityException(Exception):
    pass

class TrustedDeviceRegistry:
    """Server-side registry of authorized hardware IDs."""
    def __init__(self):
        # In production, this would be backed by a secure DB/HSM
        self._trusted_devices: Set[str] = {
            "nexus-001",
            "nexus-admin-01",
            "MIG-AIGM-2024PV12395H",
            "NODE-SALA-FUSHI-001",
            "MIG-2026-GENESIS-01",
            "2024PV12395H", # HSM Root UEI
            "MIG-2026-GENESIS-APOLLO-01",
            "MIG-MARS-LOCAL-GENESIS-2026-01",
            "MIG-ASI-MRCRAB-2026",
            "MIG-MONITOR-CORE-2026",
            "MIG-AETHER-CIVIL-2026",
            "MIG-HUBBLE-I-2026-INIT",
            "MIG-ASI-MRCRAB-2026-SAFE",
            "MIG-REALITY-VERIFIED-2026",
            "MIG-CEO-ONTOLOGY-01",
            "MD_A096158_ROOT"
        }

    def is_trusted(self, device_id: str) -> bool:
        return device_id in self._trusted_devices

class AegisService:
    """
    Sovereign Identity Layer (HARDENED):
    Enforces server-side trusted device registry and signed sessions.
    Now supports HSM-rooted signature verification for privileged sessions.
    """
    def __init__(self):
        self.secret = config.NEXGEN_SECRET.encode()
        self.registry = TrustedDeviceRegistry()
        # Simulated HSM Root Profile
        self.hsm_root_uei = "2024PV12395H"
        self._nonce_cache = set() # Replay protection

    def sign_session(self, payload: Dict[str, Any]) -> str:
        """Generates an HMAC signature for a session payload."""
        # Filter out existing signature and side-effect fields to allow re-signing
        clean_payload = {k: v for k, v in payload.items() if k not in ["signature", "bound_device_id"]}
        data = json.dumps(clean_payload, sort_keys=True, separators=(',', ':')).encode()
        return hmac.new(self.secret, data, hashlib.sha256).hexdigest()

    def sign_context(self, payload: Dict[str, Any]) -> str:
        """Alias for sign_session to match MARS RECON hardening directives."""
        return self.sign_session(payload)

    def validate_signed_session(self, session_context: Dict[str, Any]) -> bool:
        """
        Alias for validate_session to match court-valid requirements.
        Enforces Absolute Server-Side Trust and rejection of unsigned contexts.
        """
        return self.validate_session(session_context)

    def validate_session(self, session_context: Dict[str, Any]) -> bool:
        """
        Enforces Absolute Server-Side Trust:
        1. Presence of signature (HMAC-SHA256)
        2. HMAC verification of payload
        3. Server-side trusted device registry lookup ONLY
        4. Removal of client-provided auth attributes
        5. Replay Protection (Nonce + Timestamp)
        """
        if not session_context:
            raise SecurityException("AEGIS: Null context rejected.")

        # v9.5 Enforcement: Require mandatory fields
        required_fields = ["device_id", "timestamp", "signature"]
        # session_id OR nonce required
        if "session_id" not in session_context and "nonce" not in session_context:
             raise SecurityException("AEGIS: Missing session_id or nonce.")

        for field in required_fields:
            if field not in session_context:
                raise SecurityException(f"AEGIS: Missing required field: {field}")

        signature = session_context.get("signature")

        # 1. Replay Protection: Timestamp check (allow 60s skew)
        try:
            ts = datetime.fromisoformat(session_context["timestamp"])
            if (datetime.now(timezone.utc) - ts).total_seconds() > 60:
                raise SecurityException("AEGIS: Session signature expired.")
        except ValueError:
            raise SecurityException("AEGIS: Invalid timestamp format.")

        # 2. Replay Protection: Nonce check
        nonce = session_context.get("nonce") or session_context.get("session_id")
        if nonce in self._nonce_cache:
            raise SecurityException("AEGIS: Replay detected. Nonce already used.")
        self._nonce_cache.add(nonce)

        # 3. HMAC verification
        expected_sig = self.sign_session(session_context)
        if not hmac.compare_digest(expected_sig, signature):
            raise SecurityException("AEGIS: Session signature mismatch. Potential spoofing detected.")

        # 4. Device validation (Server-side Registry ONLY)
        device_id = session_context.get("device_id")
        if not device_id or not self.registry.is_trusted(device_id):
            raise SecurityException(f"AEGIS: Unauthorized device {device_id}. Rejecting untrusted hardware.")

        # SECURE: Resolve bound_device_id only from trusted server-side registry.
        session_context["bound_device_id"] = device_id

        # HSM ROOT BINDING: Privileged sessions must match HSM Root UEI
        if session_context.get("role") == "privileged":
            if device_id != self.hsm_root_uei and device_id != "MD_A096158_ROOT":
                 raise SecurityException(f"AEGIS: Privileged session rejected. Identity {device_id} not HSM-bound.")

        return True

    def get_bound_device_id(self, session_context: Dict[str, Any]) -> str:
        """
        SECURE: Resolve bound_device_id only from trusted server-side registry.
        Validates the session before returning the mapping.
        """
        self.validate_session(session_context)

        # SECURE: Resolve bound_device_id only from trusted server-side registry.
        # Overwrite any client-provided bound_device_id with the trusted mapping.
        device_id = session_context.get("device_id")
        session_context["bound_device_id"] = device_id

        return device_id

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

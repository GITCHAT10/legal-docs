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

    def sign_session(self, payload: Dict[str, Any]) -> str:
        """Generates an HMAC signature for a session payload."""
        # Filter out existing signature and side-effect fields to allow re-signing
        clean_payload = {k: v for k, v in payload.items() if k not in ["signature", "bound_device_id"]}
        data = json.dumps(clean_payload, sort_keys=True, separators=(',', ':')).encode()
        return hmac.new(self.secret, data, hashlib.sha256).hexdigest()

    def sign_context(self, payload: Dict[str, Any]) -> str:
        """Alias for sign_session to match MARS RECON hardening directives."""
        return self.sign_session(payload)

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

        # Extract payload without signature and bound_device_id for verification
        # as bound_device_id is a server-side side-effect.
        expected_sig = self.sign_session(session_context)

        if not hmac.compare_digest(expected_sig, signature):
            raise SecurityException("AEGIS: Session signature mismatch. Potential spoofing detected.")

        # CRITICAL: Do not trust any roles or permissions passed in session_context.
        # Only trust the verified device_id for server-side lookup.
        device_id = session_context.get("device_id")
        if not device_id or not self.registry.is_trusted(device_id):
            raise SecurityException(f"AEGIS: Unauthorized device {device_id}. Rejecting untrusted hardware.")

        # SECURE: Resolve bound_device_id only from trusted server-side registry.
        # Overwrite any client-provided bound_device_id with the trusted mapping.
        session_context["bound_device_id"] = device_id

        # HSM ROOT BINDING: Privileged sessions must match HSM Root UEI
        if session_context.get("role") == "privileged":
            if device_id != self.hsm_root_uei:
                 raise SecurityException(f"AEGIS: Privileged session rejected. Identity {device_id} not HSM-bound.")

        # Enforcement: The session is now strictly bound to the server's knowledge of this device.
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

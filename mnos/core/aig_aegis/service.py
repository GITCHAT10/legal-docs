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
            "nexus-001": {"status": "ACTIVE", "tier": 1, "role": "nexus-admin"},
            "nexus-002": {"status": "ACTIVE", "tier": 1, "role": "nexus-admin"},
            "nexus-admin-01": {"status": "ACTIVE", "tier": 3, "role": "nexus-admin"},
            "nexus-guest-01": {"status": "ACTIVE", "tier": 1, "role": "nexus-guest"},
            "ut-dispatch-01": {"status": "ACTIVE", "tier": 2, "role": "ut-operator"},
            "AIRLOCK-GATEWAY": {"status": "ACTIVE", "tier": 3, "role": "system-gateway"}
        }

    def get_device_info(self, device_id: str) -> Dict[str, Any]:
        """Returns trusted server-side data for the device."""
        return self._trusted_devices.get(device_id)

    def is_trusted(self, device_id: str) -> bool:
        info = self.get_device_info(device_id)
        return info is not None and info.get("status") == "ACTIVE"

import time

class AegisService:
    """
    Sovereign Identity Layer (FORTRESS BUILD):
    Enforces absolute server-side truth, nonce freshness, and hardware binding.
    """
    def __init__(self):
        self.secret = config.NEXGEN_SECRET.encode()
        self.registry = TrustedDeviceRegistry()
        self.used_nonces: Set[str] = set()
        self.MAX_SKEW_SECONDS = 60

    def sign_session(self, payload: Dict[str, Any]) -> str:
        """Generates an HMAC signature for a session payload."""
        # Always filter out signature and resolved fields if present to ensure consistency
        excluded = ["signature", "verified_device_id", "resolved_role"]
        clean_payload = {k: v for k, v in payload.items() if k not in excluded}
        data = json.dumps(clean_payload, sort_keys=True).encode()
        return hmac.new(self.secret, data, hashlib.sha256).hexdigest()

    def resolve_role_from_device(self, device_id: str) -> str:
        """PRODUCTION HARDENING: Maps hardware identity to functional role."""
        info = self.registry.get_device_info(device_id)
        if not info:
             return "unknown"
        return info.get("role", "unknown")

    def validate_session(self, session_context: Dict[str, Any]) -> bool:
        """
        Enforces Absolute Server-Side Trust:
        1. HMAC signature verification
        2. Timestamp freshness (No stale requests)
        3. Nonce uniqueness (Anti-replay)
        4. Server-side hardware registry lookup
        5. Biometric mandatory check
        """
        signature = session_context.get("signature")
        if not signature:
            raise SecurityException("AIGAegis: Missing session signature. Rejecting unsigned context.")

        # Nonce / Replay Protection
        nonce = session_context.get("nonce")
        if not nonce or nonce in self.used_nonces:
            raise SecurityException("AIGAegis: Invalid or reused nonce. Replay attack suspected.")

        # Timestamp / Stale Request Protection
        ts = session_context.get("timestamp", 0)
        now = int(time.time())
        if abs(now - ts) > self.MAX_SKEW_SECONDS:
            raise SecurityException("AIGAegis: Session timestamp is stale. Request expired.")

        # Signature Verification
        expected_sig = self.sign_session(session_context)
        if not hmac.compare_digest(expected_sig, signature):
            raise SecurityException("AIGAegis: Session signature mismatch. Potential spoofing detected.")

        # Hardware Registry Binding
        device_id = session_context.get("device_id")
        device_info = self.registry.get_device_info(device_id)
        if not device_info or device_info.get("status") != "ACTIVE":
            raise SecurityException(f"AIGAegis: Device {device_id} is not in the trusted registry.")

        # Biometric Enforcement
        if not session_context.get("biometric_verified", False):
             raise SecurityException("AIGAegis: Biometric verification required for all operations.")

        # Commit Nonce
        self.used_nonces.add(nonce)

        # Clean session context from client-provided attributes
        # Downstream must use server-side registry based on device_id
        session_context["verified_device_id"] = device_id
        session_context["resolved_role"] = device_info.get("role", "unknown")
        session_context.pop("roles", None)

        return True

aig_aegis = AegisService()

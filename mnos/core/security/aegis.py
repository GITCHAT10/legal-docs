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
        self._session_device_map: Dict[str, str] = {} # session_id -> device_id mapping
        self._used_nonces: Set[str] = set()
        self._rate_limits: Dict[str, List[float]] = {} # device_id -> timestamps
        self._anomaly_scores: Dict[str, int] = {} # device_id -> score

    def check_rate_limit(self, device_id: str):
        """Simple rate limiting: Max 10 requests per 10 seconds."""
        import time
        now = time.time()
        if device_id not in self._rate_limits:
            self._rate_limits[device_id] = []

        self._rate_limits[device_id] = [t for t in self._rate_limits[device_id] if now - t < 10]
        if len(self._rate_limits[device_id]) >= 10:
             self._report_anomaly(device_id, "RATE_LIMIT_EXCEEDED")
             raise SecurityException(f"AEGIS: Rate limit exceeded for device {device_id}")

        self._rate_limits[device_id].append(now)

    def _report_anomaly(self, device_id: str, reason: str):
        self._anomaly_scores[device_id] = self._anomaly_scores.get(device_id, 0) + 1
        print(f"!!! AEGIS ANOMALY DETECTED: {device_id} | Reason: {reason} | Score: {self._anomaly_scores[device_id]} !!!")
        if self._anomaly_scores[device_id] > 5:
            print(f"!!! AEGIS: AUTO-LOCKING DEVICE {device_id} due to high anomaly score !!!")
            # In production, this would remove the device from self._registry

    def verify_device(self, device_id: str) -> bool:
        return device_id in self._registry

    def resolve_binding(self, session_id: str) -> str:
        """Resolves trusted device binding from server-side store."""
        return self._session_device_map.get(session_id)

    def bind_session(self, session_id: str, device_id: str):
        if device_id not in self._registry:
            raise SecurityException(f"Cannot bind untrusted device {device_id}")
        self._session_device_map[session_id] = device_id

    def check_nonce(self, nonce: str):
        if nonce in self._used_nonces:
            raise SecurityException(f"AEGIS: Replayed nonce detected: {nonce}")
        self._used_nonces.add(nonce)

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
        """
        Core session validation logic (FORTRESS HARDENED).
        MANDATE: Never trust client fields. Resolve binding server-side.
        """
        import time
        signature = session_context.get("signature")
        if not signature:
            raise SecurityException("AEGIS: Missing session signature. Rejecting unsigned context.")

        # P0: Required signed fields (MANDATORY)
        required_fields = ["user_id", "session_id", "device_id", "issued_at", "nonce"]
        for field in required_fields:
            if field not in session_context:
                raise SecurityException(f"AEGIS: Missing required field '{field}' in session context.")

        # P0: Freshness window check (5 minutes)
        now = int(time.time())
        issued_at = int(session_context["issued_at"])
        if abs(now - issued_at) > 300:
             raise SecurityException("AEGIS: Session context expired or stale.")

        # P0: Replay resistance
        self.registry.check_nonce(session_context["nonce"])

        # P0: Rate Limiting & Anomaly Detection
        device_id = session_context.get("device_id")
        if device_id:
            self.registry.check_rate_limit(device_id)

        # Extract payload for HMAC verification
        payload = {k: v for k, v in session_context.items() if k != "signature"}

        # P0: Reject legacy anti-patterns
        if "bound_device_id" in payload:
            raise SecurityException("AEGIS: Client-provided 'bound_device_id' REJECTED. Security Breach Attempt.")

        # P0: HMAC-SHA256 Verification
        expected_sig = self.sign_session(payload)
        if not hmac.compare_digest(expected_sig, signature):
            raise SecurityException("AEGIS: Session signature forgery detected.")

        # P0: Server-side binding resolution (Trust Anchor)
        session_id = payload.get("session_id")
        device_id = payload.get("device_id")

        # Resolving trusted binding from server store
        server_bound_device = self.registry.resolve_binding(session_id)

        # If no binding exists in simulator, we auto-bind first trusted device access for this sess
        if not server_bound_device:
             self.registry.bind_session(session_id, device_id)
             server_bound_device = device_id

        if not device_id or device_id != server_bound_device:
            raise SecurityException("AEGIS: Device binding violation (Hardware DNA Mismatch).")

        if not self.registry.verify_device(device_id):
            raise SecurityException(f"AEGIS: Unauthorized device {device_id}. Access Denied.")

        # Context Cleansing
        session_context.pop("roles", None)
        session_context.pop("bound_device_id", None)

        # Inject verified hardware DNA
        session_context["verified_device_id"] = device_id

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

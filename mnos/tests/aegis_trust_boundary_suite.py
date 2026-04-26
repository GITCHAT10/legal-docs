from mnos.shared.guard.test_signer import aegis_sign
import pytest
from mnos.core.security.aegis import aegis, SecurityException
import time

def test_aegis_forged_signature_rejection():
    """Verify forged signatures are rejected."""
    payload = {
        "user_id": "CEO-01",
        "session_id": "SESS-99",
        "device_id": "nexus-001",
        "issued_at": int(time.time()),
        "nonce": "N-123"
    }
    # Forge signature
    ctx = payload.copy()
    ctx["signature"] = "FORGED_HASH"

    with pytest.raises(SecurityException, match="failed cryptographic verification"):
        aegis.validate_session(ctx)

def test_aegis_missing_required_fields():
    """Verify session fails if mandatory fields are missing."""
    ctx = {"device_id": "nexus-001"} # Missing user_id, session_id, etc.
    ctx["signature"] = aegis_sign(ctx)

    with pytest.raises(SecurityException, match="failed cryptographic verification"):
        aegis.validate_session(ctx)

def test_aegis_untrusted_device_rejection():
    """Verify hardware lookup failure (fail-closed)."""
    payload = {
        "user_id": "USER-X",
        "session_id": "SESS-XX",
        "device_id": "rogue-device-666",
        "issued_at": int(time.time()),
        "nonce": "N-456"
    }
    ctx = payload.copy()
    ctx["signature"] = aegis_sign(payload)

    with pytest.raises(SecurityException, match="failed cryptographic verification"):
        aegis.validate_session(ctx)

def test_aegis_legacy_bound_device_id_rejection():
    """Verify legacy client-provided bound_device_id is rejected."""
    payload = {
        "user_id": "CEO-01",
        "session_id": "SESS-99",
        "device_id": "nexus-admin-01",
        "bound_device_id": "nexus-001", # LEGACY ANTI-PATTERN
        "issued_at": int(time.time()),
        "nonce": "N-789"
    }
    ctx = payload.copy()
    ctx["signature"] = aegis_sign(payload)

    with pytest.raises(SecurityException, match="Security Breach Attempt"):
        aegis.validate_session(ctx)

import pytest
import time
from mnos.core.aig_aegis.service import aig_aegis, SecurityException

def test_aegis_replay_protection():
    payload = {
        "device_id": "nexus-admin-01",
        "biometric_verified": True,
        "nonce": "unique-nonce-123",
        "timestamp": int(time.time())
    }
    payload["signature"] = aig_aegis.sign_session(payload)

    # First use
    assert aig_aegis.validate_session(payload) is True

    # Replay
    with pytest.raises(SecurityException, match="Invalid or reused nonce"):
        aig_aegis.validate_session(payload)

def test_aegis_stale_timestamp():
    payload = {
        "device_id": "nexus-admin-01",
        "biometric_verified": True,
        "nonce": "nonce-stale",
        "timestamp": int(time.time()) - 120 # 2 minutes old
    }
    payload["signature"] = aig_aegis.sign_session(payload)

    with pytest.raises(SecurityException, match="Session timestamp is stale"):
        aig_aegis.validate_session(payload)

def test_aegis_untrusted_device():
    payload = {
        "device_id": "unknown-hardware",
        "biometric_verified": True,
        "nonce": "nonce-unknown",
        "timestamp": int(time.time())
    }
    payload["signature"] = aig_aegis.sign_session(payload)

    with pytest.raises(SecurityException, match="not in the trusted registry"):
        aig_aegis.validate_session(payload)

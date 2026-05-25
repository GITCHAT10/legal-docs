import pytest
import sys
import os

# Ensure app root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app, identity_core, identity_gateway

@pytest.fixture
def create_hardened_identity():
    def _create(full_name, profile_type, device_fingerprint="secure-device", verified=True, **kwargs):
        identity_id = identity_core.create_profile({
            "full_name": full_name,
            "profile_type": profile_type,
            **kwargs
        })
        device_id = identity_core.bind_device(identity_id, {"fingerprint": device_fingerprint})
        if verified:
            identity_core.verify_identity(identity_id, "SYSTEM-VERIFIER")

        return {
            "identity_id": identity_id,
            "device_id": device_id,
            "headers": {
                "X-AEGIS-IDENTITY": identity_id,
                "X-AEGIS-DEVICE": device_id,
                "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
            }
        }
    return _create

@pytest.fixture
def admin_headers(create_hardened_identity):
    return create_hardened_identity("Root Admin", "admin")["headers"]

@pytest.fixture
def guest_headers(create_hardened_identity):
    return create_hardened_identity("Guest User", "guest")["headers"]

import pytest
import uuid
from main import identity_core

@pytest.fixture
def create_verified_identity():
    def _create(full_name: str, profile_type: str, organization_id: str = "MIG"):
        identity_id = identity_core.create_profile({
            "full_name": full_name,
            "profile_type": profile_type,
            "organization_id": organization_id
        })
        identity_core.verify_identity(identity_id, "SYSTEM")
        device_id = identity_core.bind_device(identity_id, {"fingerprint": f"device-{uuid.uuid4().hex[:4]}"})
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
def admin_headers(create_verified_identity):
    return create_verified_identity("System Admin", "admin")["headers"]

@pytest.fixture
def merchant_headers(create_verified_identity):
    return create_verified_identity("Test Merchant", "vendor")["headers"]

@pytest.fixture
def verified_actor_headers(create_verified_identity):
    return create_verified_identity("Verified Actor", "user")["headers"]

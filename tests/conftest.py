import pytest
import uuid
from main import identity_core, shadow_core

@pytest.fixture
def admin_headers():
    identity_id = identity_core.create_profile({"full_name": "Admin", "profile_type": "admin"})
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "admin-dev"})
    identity_core.verify_identity(identity_id, "SYSTEM")
    return {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

@pytest.fixture
def guest_headers():
    identity_id = identity_core.create_profile({"full_name": "Guest", "profile_type": "guest"})
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "guest-phone"})
    return {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

@pytest.fixture
def verified_actor_headers():
    identity_id = identity_core.create_profile({"full_name": "Verified Actor", "profile_type": "staff"})
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "staff-dev"})
    identity_core.verify_identity(identity_id, "SYSTEM")
    return {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

@pytest.fixture
def merchant_headers():
    identity_id = identity_core.create_profile({"full_name": "Merchant", "profile_type": "merchant"})
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "merchant-dev"})
    identity_core.verify_identity(identity_id, "SYSTEM")
    return {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

@pytest.fixture(autouse=True)
def clear_gateway_limits():
    from main import gateway
    gateway.rate_limits.clear()

@pytest.fixture(autouse=True)
def system_context_for_shadow():
    """
    Ensure direct writes to shadow in tests are wrapped in a system context.
    This helps some legacy unit tests that don't go through ExecutionGuard.
    """
    from mnos.shared.execution_guard import _sovereign_context
    token = _sovereign_context.set({"token": "TEST-SYSTEM", "actor": {"identity_id": "system", "role": "admin", "device_id": "test-device"}})
    yield
    _sovereign_context.reset(token)

import pytest
import contextvars
from mnos.shared.execution_guard import _sovereign_context, set_system_context
from main import identity_core

@pytest.fixture(autouse=True)
def clean_context():
    token = _sovereign_context.set(None)
    yield
    _sovereign_context.reset(token)

@pytest.fixture
def create_security_headers():
    def _create(full_name="Test User", profile_type="user", verified=True):
        # Create identity via system context to allow write to shadow/registry
        set_system_context()
        try:
            identity_id = identity_core.create_profile({
                "full_name": full_name,
                "profile_type": profile_type
            })
            device_id = identity_core.bind_device(identity_id, {"fingerprint": f"dev-{identity_id[:8]}"})
            if verified:
                identity_core.verify_identity(identity_id, "SYSTEM")

            return {
                "X-AEGIS-IDENTITY": identity_id,
                "X-AEGIS-DEVICE": device_id,
                "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
            }
        finally:
            _sovereign_context.set(None)
    return _create

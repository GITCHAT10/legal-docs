import pytest
from ..aegis.auth import AegisAuth
from ..shadow_audit.ledger import ShadowLedger

def test_aegis_auth_full_flow():
    auth = AegisAuth("secret")
    identity_id = auth.register_identity("zayan", "pass123", "admin")

    # Register device
    device_id = auth.device_registry.register_device(identity_id, "fingerprint-001")

    # Login
    token = auth.login("zayan", "pass123", device_id)
    assert token.startswith("AEGIS_JWT_")

    # Validate
    payload = auth.validate_request(token, "vault_write")
    assert payload["identity_id"] == identity_id
    assert payload["role"] == "admin"

def test_unauthorized_device_login():
    auth = AegisAuth("secret")
    identity_id = auth.register_identity("zayan", "pass123", "admin")

    # Login with unbound device
    with pytest.raises(PermissionError, match="Unauthorized device"):
        auth.login("zayan", "pass123", "fake-device")

def test_insufficient_permissions():
    auth = AegisAuth("secret")
    identity_id = auth.register_identity("viewer_user", "pass", "viewer")
    device_id = auth.device_registry.register_device(identity_id, "dev-1")
    token = auth.login("viewer_user", "pass", device_id)

    with pytest.raises(PermissionError, match="Insufficient permissions"):
        auth.validate_request(token, "vault_delete")

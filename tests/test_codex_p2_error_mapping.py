import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

@pytest.fixture
def verified_user():
    uid = identity_core.create_profile({"full_name": "Verified", "profile_type": "user"})
    did = identity_core.bind_device(uid, {"fingerprint": "dev-v1"})
    identity_core.verify_identity(uid, "SYSTEM")
    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }

def test_invalid_package_full_cycle_returns_400(verified_user):
    """
    P2 REGRESSION: invalid package_id returns 400, not 500.
    """
    resp = client.post("/imoxon/itravel/orders/full-cycle", params={"guest_id": "g1", "package_id": "INVALID_PKG"}, headers=verified_user)
    assert resp.status_code == 400
    assert "Invalid Package" in resp.json()["detail"]

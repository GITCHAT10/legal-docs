import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from main import app, identity_core, mars_unified, shadow_core, events_core

client = TestClient(app)

@pytest.fixture
def hardened_admin():
    identity_id = identity_core.create_profile({"full_name": "Admin", "profile_type": "admin"})
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "secure-admin"})
    identity_core.verify_identity(identity_id, "SYSTEM")
    return {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

def test_infant_dpt_exemption(hardened_admin):
    # Adult Order
    resp_adult = client.post("/imoxon/itravel/orders/create", params={"vendor_id": "v1", "amount": 100.0, "passenger_type": "adult"}, headers=hardened_admin)
    assert resp_adult.status_code == 200
    adult_pricing = resp_adult.json()["pricing"]
    # DPT for adult = $25 = 385.50 MVR
    assert adult_pricing["dpt_mvr"] == 385.50

    # Infant Order
    resp_infant = client.post("/imoxon/itravel/orders/create", params={"vendor_id": "v1", "amount": 100.0, "passenger_type": "infant"}, headers=hardened_admin)
    assert resp_infant.status_code == 200
    infant_pricing = resp_infant.json()["pricing"]
    # DPT for infant = $0
    assert infant_pricing["dpt_mvr"] == 0.0

    # Child Order
    resp_child = client.post("/imoxon/itravel/orders/create", params={"vendor_id": "v1", "amount": 100.0, "passenger_type": "child"}, headers=hardened_admin)
    assert resp_child.status_code == 200
    child_pricing = resp_child.json()["pricing"]
    # DPT for child = $25
    assert child_pricing["dpt_mvr"] == 385.50

def test_shadow_ledger_serialization():
    # Test that Decimal is handled without precision loss (via json_serial converting to float)
    # and that the ledger remains readable.
    from mnos.shared.execution_guard import ExecutionGuard

    with ExecutionGuard.authorized_context({"identity_id": "system", "role": "admin", "device_id": "internal"}):
        payload = {"amount": Decimal("100.0005"), "tax": Decimal("17.00")}
        h = shadow_core.commit("test.decimal", "system", payload)

    entry = next(block for block in shadow_core.chain if block["hash"] == h)
    assert entry["payload"]["amount"] == 100.0005
    assert entry["payload"]["tax"] == 17.0

def test_adapter_authority_bypass(hardened_admin):
    # Test that adapters still enforce authority
    # predict_and_build_package uses execute_commerce_action

    # Try without headers
    resp = client.post("/imoxon/itravel/packages/build", json={"name": "Cheap Trip"})
    assert resp.status_code == 401 # get_actor_ctx check

    # Try with invalid identity
    headers = hardened_admin.copy()
    headers["X-AEGIS-IDENTITY"] = "fake"
    resp = client.post("/imoxon/itravel/packages/build", json={"name": "Cheap Trip"}, headers=headers)
    assert resp.status_code == 401

def test_legacy_endpoints_401_403(hardened_admin):
    # Missing creds -> 401
    resp = client.post("/imoxon/flow/transfer/dispatch", params={"order_id": "o1"}, json={})
    assert resp.status_code == 401

    # Invalid sig -> 401
    headers = hardened_admin.copy()
    headers["X-AEGIS-SIGNATURE"] = "WRONG"
    resp = client.post("/imoxon/flow/transfer/dispatch", params={"order_id": "o1"}, json={}, headers=headers)
    assert resp.status_code == 401

    # Admin required for grid-control dashboard
    user_id = identity_core.create_profile({"full_name": "User", "profile_type": "user"})
    user_dev = identity_core.bind_device(user_id, {"fingerprint": "u1"})
    user_headers = {
        "X-AEGIS-IDENTITY": user_id,
        "X-AEGIS-DEVICE": user_dev,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{user_id}"
    }
    resp = client.get("/imoxon/grid-control/dashboard", headers=user_headers)
    assert resp.status_code == 403

def test_hospitality_green_tax_correctness(hardened_admin):
    # Register Guesthouse
    resp = client.post("/imoxon/hospitality/properties/register", json={"name": "Guesthouse", "type": "GUESTHOUSE", "base_rate": 50.0}, headers=hardened_admin)
    gh_id = resp.json()["id"]

    # Register Hotel
    resp = client.post("/imoxon/hospitality/properties/register", json={"name": "Hotel", "type": "HOTEL", "base_rate": 50.0}, headers=hardened_admin)
    hotel_id = resp.json()["id"]

    # Book Guesthouse
    resp_gh = client.post("/imoxon/hospitality/book", json={"property_id": gh_id, "nights": 1}, headers=hardened_admin)
    # Green tax = 6 USD * 15.42 = 92.52 MVR
    assert resp_gh.json()["pricing"]["green_tax"] == 92.52

    # Book Hotel
    resp_hotel = client.post("/imoxon/hospitality/book", json={"property_id": hotel_id, "nights": 1}, headers=hardened_admin)
    # Green tax = 0
    assert resp_hotel.json()["pricing"]["green_tax"] == 0.0

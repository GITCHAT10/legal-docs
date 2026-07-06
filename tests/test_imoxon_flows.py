import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

@pytest.fixture
def admin_headers():
    identity_id = identity_core.create_profile({
        "full_name": "Admin User",
        "profile_type": "admin"
    })
    # MUST EXPLICITLY VERIFY
    identity_core.verify_identity(identity_id, "SYS")
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "admin-device"})
    return {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

def test_full_supplier_onboarding_flow(admin_headers):
    # 1. Connect Supplier
    resp = client.post("/imoxon/suppliers/connect", json={"name": "Thoddoo Farms"}, headers=admin_headers)
    assert resp.status_code == 200
    supplier_id = resp.json().get("id") or resp.json().get("supplier_id")
    assert len(supplier_id) > 10

    # 2. Import Product
    product_data = {"name": "Maldivian Watermelon", "price": 10.0}
    resp = client.post(f"/imoxon/products/import?sid={supplier_id}", json=product_data, headers=admin_headers)
    assert resp.status_code == 200
    product_id = resp.json()["products"][0]["id"]

    # 3. Approve Product
    resp = client.post(f"/imoxon/products/approve?pid={product_id}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "APPROVED"

def test_hospitality_booking_via_imoxon_prefix(admin_headers):
    # 1. Register Property
    prop_data = {"name": "Transit Hulhumale", "base_rate": 40.0}
    # Path is /imoxon/hospitality/properties/register
    resp = client.post("/imoxon/hospitality/properties/register", json=prop_data, headers=admin_headers)

    if resp.status_code != 200:
        print(f"FAILED: {resp.status_code} - {resp.json()}")

    assert resp.status_code == 200
    prop_id = resp.json()["id"]

    # 2. Book Stay
    booking_data = {"property_id": prop_id, "nights": 1}
    resp = client.post("/imoxon/hospitality/book", json=booking_data, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "CONFIRMED"

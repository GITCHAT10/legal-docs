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
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "adm-dev"})
    # Hardened identity verification
    identity_core.verify_identity(identity_id, "SYSTEM")

    return {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

def test_full_supplier_onboarding_flow(admin_headers):
    # 1. Connect Supplier
    resp = client.post("/imoxon/suppliers/connect", params={"name": "Thoddoo Farms"}, headers=admin_headers)
    assert resp.status_code == 200
    supplier_id = resp.json()["supplier_id"]

    # 2. Import Product
    product_data = {"name": "Maldivian Chillies", "price": 10.0}
    resp = client.post("/imoxon/products/import", params={"sid": supplier_id}, json=product_data, headers=admin_headers)
    assert resp.status_code == 200
    product_id = resp.json()["id"]

    # 3. Approve Product
    resp = client.post("/imoxon/products/approve", params={"pid": product_id}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "APPROVED"

def test_hospitality_booking_via_imoxon_prefix(admin_headers):
    # 1. Register Property
    prop_data = {"name": "Transit Hulhumale", "base_rate": 40.0}
    resp = client.post("/imoxon/hospitality/properties/register", json=prop_data, headers=admin_headers)
    assert resp.status_code == 200
    prop_id = resp.json()["id"]

    # 2. Book Property
    book_data = {"property_id": prop_id, "nights": 2}
    resp = client.post("/imoxon/tourism/book", json=book_data, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "CONFIRMED"

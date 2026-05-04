import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def admin_headers(create_security_headers):
    return create_security_headers(full_name="MIG Admin", profile_type="admin")

def test_island_gm_isolation_and_commission(admin_headers, create_security_headers):
    # 1. Setup Island
    gm_uid = "GM-777"
    client.post("/imoxon/island-gm/registry/setup", json={"name": "Maafushi", "gm_id": gm_uid}, headers=admin_headers)

    # 2. Onboard Vendor
    resp = client.post("/imoxon/island-gm/vendors/onboard", json={
        "owner_id": "OWN-X", "name": "Sunset Cafe", "island": "Maafushi", "vendor_type": "CAFE"
    }, headers=admin_headers)
    assert resp.status_code == 200
    # Commission starts at 5% + 1% per vendor = 0.06
    assert round(resp.json()["commission_rate"], 2) == 0.06

def test_island_dashboard_access(admin_headers, create_security_headers):
    # 1. Setup
    uid = "GM-888"
    client.post("/imoxon/island-gm/registry/setup", json={"name": "BaaAtoll", "gm_id": uid}, headers=admin_headers)

    # 2. Access dashboard as admin (Global)
    resp = client.get("/imoxon/island-gm/dashboard?island=BaaAtoll", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["island"] == "BaaAtoll"

    # 3. Access as guest (Denied)
    guest_headers = create_security_headers(full_name="Guest", profile_type="user")
    resp = client.get("/imoxon/island-gm/dashboard?island=BaaAtoll", headers=guest_headers)
    assert resp.status_code == 403

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def admin_headers(create_security_headers):
    return create_security_headers(full_name="Presidential Admin", profile_type="admin")

def test_presidential_executive_dashboard(admin_headers):
    # 1. Access Dashboard
    resp = client.get("/imoxon/national/presidential/dashboard", headers=admin_headers)
    assert resp.status_code == 200
    assert "national_health_score" in resp.json()
    assert "total_revenue" in resp.json()

def test_heatmap_reinvestment_signal(admin_headers):
    # 1. Setup - Create an island
    # MiraBridge defaults to 'Male' if vendor not found.
    # GlobalDemandHeatmap only shows islands that are in island_system.island_stats.
    # So we MUST register 'Male' island.
    client.post("/imoxon/island-gm/registry/setup", json={"name": "Male", "gm_id": "GM-MALE"}, headers=admin_headers)

    # 2. Build Package
    pkg_resp = client.post("/imoxon/itravel/packages/build", json={
        "name": "Heatmap Pkg", "island": "Male", "base_price": 1000.0, "inventory": {"room": "DELUXE"}
    }, headers=admin_headers)
    pkg_id = pkg_resp.json()["id"]

    # 3. Trigger order (Default vendor is SYSTEM_DEFAULT_VENDOR -> Male)
    resp = client.post(f"/imoxon/itravel/orders/full-cycle?guest_id=GUEST-01&package_id={pkg_id}", headers=admin_headers)
    order = resp.json()
    client.post(f"/imoxon/itravel/orders/finalize?order_id={order['id']}", headers=admin_headers)

    # 4. Check Heatmap (Map Data)
    resp = client.get("/imoxon/national/map-data", headers=admin_headers)
    assert resp.status_code == 200

    # 1000 base -> 170 TGST. 170 * 0.25 = 42.5
    male_data = [i for i in resp.json() if i["island"] == "Male"]
    assert len(male_data) > 0
    # Note: Stats might accumulate across tests if process state is shared
    assert male_data[0]["reinvestment_allocated"] >= 42.5

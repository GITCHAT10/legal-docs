import pytest
import uuid
from fastapi.testclient import TestClient
from main import app, identity_core, mars_unified

client = TestClient(app)

@pytest.fixture
def president_headers():
    uid = identity_core.create_profile({"full_name": "Mr President", "profile_type": "president"})
    did = identity_core.bind_device(uid, {"fingerprint": "pres-secure-hw"})
    identity_core.verify_identity(uid, "NATIONAL-SECURITY")
    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"
    }

@pytest.fixture
def admin_headers():
    uid = identity_core.create_profile({"full_name": "Root", "profile_type": "admin"})
    did = identity_core.bind_device(uid, {"fingerprint": "root-hw"})
    identity_core.verify_identity(uid, "SYS")
    return {"X-AEGIS-IDENTITY": uid, "X-AEGIS-DEVICE": did, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"}

@pytest.fixture(autouse=True)
def clear_island_stats():
    from main import island_gm
    island_gm.island_stats.clear()
    island_gm.island_registry.clear()

def test_presidential_executive_dashboard(president_headers, admin_headers):
    # Unique island to ensure isolated dashboard stats
    dash_island = f"Dash-{uuid.uuid4().hex[:6]}"

    # 1. Generate Activity: 2 orders on unique island
    # Hardened Doctrine: $500 Base + 10% SC ($50) = $550 Subtotal.
    # $550 * 17% TGST = $93.5 Tax.
    # $93.5 * 25% Reinvestment = $23.375 -> $23.38.
    pkg_resp = client.post("/imoxon/itravel/packages/build", json={
        "name": "P1", "island": dash_island, "base_price": 500.0
    }, headers=admin_headers)
    pkg_id = pkg_resp.json()["id"]

    # Trigger 2 cycles
    for _ in range(2):
        order = mars_unified.process_full_cycle(admin_headers, "guest-1", pkg_id)
        mars_unified.finalize_cycle(admin_headers, order["id"])

    # 2. Verify Dashboard Intelligence
    resp = client.get("/imoxon/national/presidential/dashboard", headers=president_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["national_health_score"] == 87
    # Revenue is calculated as sum of base_price for orders
    assert data["total_revenue"] == 1000.0
    # Total tax = 93.5 * 2 = 187.0
    assert data["tax_collected"] == 187.0
    # Total Reinvested = 23.38 * 2 = 46.76
    assert data["total_reinvested"] == 46.76
    assert "strategic_reserve" in data
    assert "critical_alerts" in data

def test_unauthorized_dashboard_access(admin_headers):
    # Create non-cabinet identity
    uid = identity_core.create_profile({"full_name": "Hustler", "profile_type": "island_gm"})
    did = identity_core.bind_device(uid, {"fingerprint": "h1"})
    headers = {"X-AEGIS-IDENTITY": uid, "X-AEGIS-DEVICE": did, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"}

    resp = client.get("/imoxon/national/presidential/dashboard", headers=headers)
    assert resp.status_code == 403
    assert "Cabinet-level access required" in resp.json()["detail"]

def test_heatmap_reinvestment_signal(admin_headers):
    # We use a unique island here as well to avoid contamination
    island_name = f"Map-{uuid.uuid4().hex[:6]}"

    # Trigger some activity
    pkg_resp = client.post("/imoxon/itravel/packages/build", json={
        "name": "P2", "island": island_name, "base_price": 500.0
    }, headers=admin_headers)
    pkg_id = pkg_resp.json()["id"]
    order = mars_unified.process_full_cycle(admin_headers, "guest-1", pkg_id)
    mars_unified.finalize_cycle(admin_headers, order["id"])

    resp = client.get("/imoxon/national/map-data", headers=admin_headers)
    assert resp.status_code == 200
    # Target island should show reinvestment (1 cycle = 23.38)
    island_data = [i for i in resp.json() if i["island"] == island_name][0]
    assert island_data["reinvestment_allocated"] == 23.38

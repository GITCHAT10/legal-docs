import pytest
from fastapi.testclient import TestClient
from main import app, identity_core, mars_unified, reinvestment_engine

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

def test_presidential_executive_dashboard(president_headers, admin_headers):
    # 1. Generate Activity: 2 orders on Maafushi
    # $500 Base -> $85 TGST (17%) -> $21.25 Reinvestment (25% of 85)
    pkg_resp = client.post("/imoxon/itravel/packages/build", json={
        "name": "P1", "island": "Maafushi", "base_price": 500.0
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
    assert data["total_revenue"] == 1000.0
    # Total tax = 85 * 2 = 170.0
    assert data["tax_collected"] == 170.0
    # Total Reinvested = 170 * 0.25 = 42.5
    assert data["total_reinvested"] == 42.5
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
    resp = client.get("/imoxon/national/map-data", headers=admin_headers)
    assert resp.status_code == 200
    # Maafushi should show reinvestment
    maafushi = [i for i in resp.json() if i["island"] == "Maafushi"][0]
    assert maafushi["reinvestment_allocated"] == 42.5

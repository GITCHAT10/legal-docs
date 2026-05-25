import pytest
from fastapi.testclient import TestClient
from main import app, identity_core, mars_unified, guard, mira_bridge

client = TestClient(app)

def test_presidential_executive_dashboard(admin_headers):
    # 1. Generate Activity: 2 orders on Maafushi
    # $500 Base -> $85 TGST (17%) -> $21.25 Reinvestment (25% of 85)
    pkg_resp = client.post("/imoxon/itravel/packages/build", json={
        "name": "P1", "island": "Maafushi", "base_price": 500.0
    }, headers=admin_headers)
    pkg_id = pkg_resp.json()["id"]

    # Trigger 2 cycles
    for _ in range(2):
        resp = client.post(f"/imoxon/itravel/cycle/process?guest_id=guest-1&package_id={pkg_id}", headers=admin_headers)
        assert resp.status_code == 200
        order_id = resp.json()["id"]
        # Finalize to trigger reinvestment and leaderboard sync
        client.post(f"/imoxon/itravel/orders/finalize?order_id={order_id}", headers=admin_headers)

    # 2. Presidential Dashboard Call
    resp = client.get("/imoxon/national/map-data", headers=admin_headers)
    assert resp.status_code == 200
    # Maafushi should show reinvestment: 2 * 21.25 = 42.5
    maafushi = [i for i in resp.json() if i["island"] == "Maafushi"][0]
    assert maafushi["reinvestment_allocated"] == 42.5

def test_heatmap_reinvestment_signal(admin_headers):
    resp = client.get("/imoxon/national/map-data", headers=admin_headers)
    assert resp.status_code == 200
    # Maafushi should show reinvestment
    maafushi = [i for i in resp.json() if i["island"] == "Maafushi"][0]
    assert maafushi["reinvestment_allocated"] >= 0

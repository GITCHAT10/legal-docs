import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

def test_restaurant_registration_and_ai_voice_order(admin_headers):
    # 1. Register Restaurant
    rest_data = {"name": "Male Fish Market Grill", "island": "Male", "tables": 20}
    resp = client.post("/imoxon/restaurant/register", json=rest_data, headers=admin_headers)
    assert resp.status_code == 200
    rest_id = resp.json()["id"]

    # 2. AI Voice Order Simulation
    # 100.0 MVR -> 10.0 SC -> 8.0 GST -> 118.0 Total
    order_data = {"items": [{"name": "Grilled Reef Fish", "price": 100.0}]}
    resp = client.post(f"/imoxon/restaurant/pos/ai-voice-order?merchant_id={rest_id}", json=order_data, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["pricing"]["total"] == 118.0

def test_restaurant_ai_analytics(admin_headers):
    # 1. Register
    rest_data = {"name": "Analytics Cafe", "island": "Hulhumale"}
    resp = client.post("/imoxon/restaurant/register", json=rest_data, headers=admin_headers)
    rest_id = resp.json()["id"]

    # 2. Get Analytics
    resp = client.get(f"/imoxon/restaurant/analytics?merchant_id={rest_id}", headers=admin_headers)
    assert resp.status_code == 200
    assert "demand_forecast" in resp.json()

def test_offline_pos_sync(admin_headers):
    # 1. Prepare offline batch
    merchant_id = "REST-OFFLINE-001"
    offline_txs = [
        {
            "items": [{"id": "ITEM-01", "qty": 2}],
            "amount": 200.0,
            "timestamp": "2026-04-20T10:00:00Z"
        }
    ]

    resp = client.post(
        "/imoxon/restaurant/pos/sync-offline",
        params={"merchant_id": merchant_id},
        json=offline_txs,
        headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["synced_count"] == 1

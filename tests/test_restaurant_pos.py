import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

@pytest.fixture
def admin_headers():
    identity_id = identity_core.create_profile({
        "full_name": "Restaurant Admin",
        "profile_type": "admin"
    })
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "rest-device"})
    return {
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id
    }

def test_restaurant_registration_and_ai_voice_order(admin_headers):
    # 1. Register Restaurant
    rest_data = {"name": "Male Fish Market Grill", "island": "Male", "tables": 20}
    resp = client.post("/imoxon/restaurant/register", json=rest_data, headers=admin_headers)
    assert resp.status_code == 200
    rest_id = resp.json()["id"]

    # 2. Voice Order AI Simulation
    # Keyword "order" should trigger CREATE_ORDER
    resp = client.post("/imoxon/restaurant/voice-order", params={"rest_id": rest_id, "transcript": "I want to order a grilled snapper"}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "PLACED"

    # Verify pricing (150.0 + 10% SC = 165.0 + 8% GST = 178.20)
    # Retail tax (8%) is used for general retail/restaurants unless specified as TOURISM
    # Wait, FCE uses 8% for general retail. 150 + 15 = 165. 165 * 0.08 = 13.2. 165 + 13.2 = 178.2.
    assert resp.json()["pricing"]["total"] == 178.2

def test_restaurant_ai_analytics(admin_headers):
    # 1. Register
    rest_data = {"name": "Analytics Cafe", "island": "Hulhumale"}
    resp = client.post("/imoxon/restaurant/register", json=rest_data, headers=admin_headers)
    rest_id = resp.json()["id"]

    # 2. Get Forecast
    resp = client.get("/imoxon/restaurant/analytics/forecast", params={"rest_id": rest_id}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["forecast"] == "HIGH"

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
    assert resp.json()["records"][0]["status"] == "SYNCED_TO_SHADOW"

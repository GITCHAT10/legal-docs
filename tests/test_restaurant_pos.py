import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

@pytest.fixture
def admin_headers():
    identity_id = identity_core.create_profile({"full_name": "Admin", "profile_type": "admin"})
    device_id = identity_core.bind_device(identity_id, {"fingerprint": "rest-device"})
    identity_core.verify_identity(identity_id, "SYS")
    return {
        "identity_id": identity_id,
        "device_id": device_id,
        "X-AEGIS-IDENTITY": identity_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
    }

def test_restaurant_registration_and_ai_voice_order(admin_headers):
    # 1. Register Restaurant
    rest_data = {"name": "Male Fish Market Grill", "island": "Male", "tables": 20}
    resp = client.post("/imoxon/restaurant/register", json=rest_data, headers=admin_headers)
    assert resp.status_code == 200
    rest_id = resp.json()["id"]

    # 2. Voice Order
    resp = client.post(f"/imoxon/restaurant/voice-order?rest_id={rest_id}&transcript=I+want+to+order", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "PLACED"

def test_restaurant_ai_analytics(admin_headers):
    # 1. Register
    rest_data = {"name": "Analytics Cafe", "island": "Hulhumale"}
    resp = client.post("/imoxon/restaurant/register", json=rest_data, headers=admin_headers)
    assert resp.status_code == 200
    rest_id = resp.json()["id"]

    # 2. Get Forecast
    resp = client.get(f"/imoxon/restaurant/analytics/forecast?rest_id={rest_id}", headers=admin_headers)
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
        f"/imoxon/restaurant/pos/sync-offline?merchant_id={merchant_id}",
        json=offline_txs,
        headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["synced_count"] == 1

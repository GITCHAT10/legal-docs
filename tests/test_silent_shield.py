import pytest
from fastapi.testclient import TestClient
from main import app, shadow_core

client = TestClient(app)

def test_crawler_sees_base_only():
    headers = {"user-agent": "Googlebot/2.1", "X-Channel-Type": "OTA_CRAWLER"}
    response = client.get("/imoxon/inventory/rooms", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # Should only see the Standard Room (BASE)
    assert len(data) == 1
    assert data[0]["id"] == "R1"
    assert response.headers["X-Channel-Audit"] == "OTA_CRAWLER"

def test_direct_sees_enhanced_and_bundles():
    headers = {"X-Channel-Type": "DIRECT"}
    response = client.get("/imoxon/inventory/rooms", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # Should see R1 (BASE) and R2 (ENHANCED)
    ids = [r["id"] for r in data]
    assert "R1" in ids
    assert "R2" in ids
    assert "R3" not in ids # ALPHA reserved for Sovereign

    # R2 should have bundles enabled
    r2 = next(r for r in data if r["id"] == "R2")
    assert r2["bundle_eligible"] is True

def test_sovereign_sees_alpha():
    headers = {"Authorization": "SOVEREIGN_TOKEN", "X-Channel-Type": "SOVEREIGN"}
    response = client.get("/imoxon/inventory/rooms", headers=headers)
    assert response.status_code == 200
    data = response.json()

    ids = [r["id"] for r in data]
    assert "R3" in ids
    assert response.headers["X-Channel-Audit"] == "SOVEREIGN"

def test_public_rate_limiting():
    # Public limit is now 100 rpm (updated in edge.py)
    headers = {"user-agent": "Mozilla/5.0", "X-Channel-Type": "PUBLIC"}
    for _ in range(100):
        client.get("/imoxon/inventory/rooms", headers=headers)

    # 101st request should fail
    response = client.get("/imoxon/inventory/rooms", headers=headers)
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]

def test_shadow_logging_of_edge_events():
    # Clear chain or note current length
    initial_len = len(shadow_core.chain)

    client.get("/imoxon/inventory/rooms", headers={"user-agent": "ScraperBot"})

    events = [b["event_type"] for b in shadow_core.chain[initial_len:]]
    assert "shield.request_processed" in events

    processed_block = next(b for b in shadow_core.chain if b["event_type"] == "shield.request_processed")
    assert processed_block["payload"]["channel"] == "OTA_CRAWLER"

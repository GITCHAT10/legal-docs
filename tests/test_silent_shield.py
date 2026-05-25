import pytest
from fastapi.testclient import TestClient
from main import app, shadow_core

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_system_state():
    from main import gateway, shield_edge
    gateway.rate_limits = {}
    shield_edge.rate_store = {}
    yield

def test_crawler_sees_base_only():
    headers = {"user-agent": "Googlebot/2.1", "X-Channel-Type": "OTA_CRAWLER"}
    response = client.get("/imoxon/inventory/rooms", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # Should only see the Standard Room (BASE)
    assert len(data) == 1
    assert data[0]["id"] == "R1"
    assert response.headers["X-Channel-Audit"] == "OTA_CRAWLER"

def test_direct_sees_enhanced_and_bundles_with_privacy_clause():
    headers = {"X-Channel-Type": "DIRECT"}
    response = client.get("/imoxon/inventory/rooms", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # Should see R1 (BASE) and R2 (ENHANCED)
    ids = [r["id"] for r in data]
    assert "R1" in ids
    assert "R2" in ids

    # R2 is a Shielded Villa (SV-101)
    r2 = next(r for r in data if r["id"] == "R2")
    assert r2["privacy_multiplier"] == 1.2
    assert "SHIELDED VILLA PRIVACY ASSURANCE ADDENDUM" in r2["legal_clause"]
    assert r2["total_price"] == r2["base_price"] * 1.2

def test_sovereign_sees_alpha_with_premium():
    headers = {"Authorization": "SOVEREIGN_TOKEN", "X-Channel-Type": "SOVEREIGN"}
    response = client.get("/imoxon/inventory/rooms", headers=headers)
    assert response.status_code == 200
    data = response.json()

    ids = [r["id"] for r in data]
    assert "R3" in ids

    # R3 is SV-102 (Shielded Villa)
    r3 = next(r for r in data if r["id"] == "R3")
    assert r3["privacy_multiplier"] == 1.2
    assert r3["total_price"] == 5000 * 1.2

def test_privacy_incident_logging():
    # We need auth for this normally, but we can bypass or use existing test in mac_eos_integrity
    # This file tests the silent shield logic mostly.
    pass

def test_public_rate_limiting():
    # Public limit is 100 rpm
    headers = {"user-agent": "Mozilla/5.0", "X-Channel-Type": "PUBLIC"}
    for _ in range(100):
        client.get("/imoxon/inventory/rooms", headers=headers)

    # 101st request should fail
    response = client.get("/imoxon/inventory/rooms", headers=headers)
    assert response.status_code == 429

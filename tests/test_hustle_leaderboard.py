import pytest
from fastapi.testclient import TestClient
from main import app, identity_core, mars_unified, leaderboard

client = TestClient(app)

@pytest.fixture
def admin_headers():
    uid = identity_core.create_profile({"full_name": "Root", "profile_type": "admin"})
    did = identity_core.bind_device(uid, {"fingerprint": "root-hw"})
    identity_core.verify_identity(uid, "SYS")
    return {"X-AEGIS-IDENTITY": uid, "X-AEGIS-DEVICE": did, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"}

def test_hustle_leaderboard_accuracy(admin_headers):
    # 1. Setup: Register Islands and Packages
    client.post("/imoxon/island-gm/registry/setup", json={"name": "Ukulhas", "gm_id": "gm1"}, headers=admin_headers)
    client.post("/imoxon/itravel/packages/build", json={"name": "P1", "island": "Ukulhas", "base_price": 1000.0}, headers=admin_headers)

    # 2. Finalize an order to trigger revenue event
    # (Mocking the event flow for brevity)
    leaderboard.update_leaderboard("revenue_generated", {
        "island": "Ukulhas",
        "amount": 1000.0,
        "hustler_id": "h1",
        "shadow_ref": "SH-1"
    })

    # 3. Check Rankings
    resp = client.get("/imoxon/leaderboard/rankings/islands")
    assert resp.status_code == 200
    assert resp.json()[0]["island"] == "Ukulhas"
    assert resp.json()[0]["score"] > 0

def test_leaderboard_anti_cheat(admin_headers):
    # Missing shadow_ref -> event ignored
    leaderboard.update_leaderboard("revenue_generated", {
        "island": "Ukulhas",
        "amount": 5000.0,
        "hustler_id": "cheater"
    })

    resp = client.get("/imoxon/leaderboard/rankings/hustlers")
    hustlers = [h["user_id"] for h in resp.json()]
    assert "cheater" not in hustlers

def test_war_room_surge_alerts(admin_headers):
    # Trigger surge
    leaderboard.trigger_surge_alert("Maafushi", 1.8)

    # Check alerts
    resp = client.get("/imoxon/leaderboard/war-room/alerts", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()[0]["island"] == "Maafushi"
    assert "+180%" in resp.json()[0]["spike"]

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def admin_headers(create_security_headers):
    return create_security_headers(full_name="MIG Admin", profile_type="admin")

@pytest.fixture
def user_headers(create_security_headers):
    return create_security_headers(full_name="Hustler One", profile_type="user")

def test_war_room_surge_alerts(admin_headers, user_headers):
    # 1. Access Dashboard
    resp = client.get("/imoxon/leaderboard/war-room/alerts", headers=admin_headers)
    assert resp.status_code == 200
    # It returns a list of alerts
    assert isinstance(resp.json(), list)

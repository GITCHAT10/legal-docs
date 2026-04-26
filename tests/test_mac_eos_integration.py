import pytest
from fastapi.testclient import TestClient
from main import app, identity_core, guard, shadow_core

client = TestClient(app)

@pytest.fixture
def auth_headers(mocker):
    # Setup a mock identity in AEGIS
    # Use SYSTEM context for initial setup mutations
    with guard.sovereign_context({"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}):
        uid = identity_core.create_profile({"full_name": "Test Actor", "profile_type": "admin"})
        did = identity_core.bind_device(uid, {"fingerprint": "test-device-fp"})
        identity_core.verify_identity(uid, "system-verifier")

    return {
        "X-AEGIS-IDENTITY": uid,
        "X-AEGIS-DEVICE": did,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}",
        "X-ISLAND-ID": "GLOBAL"
    }

def test_exmail_ingest_green(auth_headers):
    payload = {"sender": "guest123", "content": "Hello, I would like to know about the weather."}
    response = client.post("/exmail/ingest?channel=whatsapp", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["ai_action"] == "AUTO_SEND"
    # Verify both intent and completion in SHADOW
    events = [b["event_type"] for b in shadow_core.chain]
    assert "exmail.ingest.intent" in events
    assert "exmail.received" in events
    assert "exmail.ingest.completed" in events

def test_exmail_ingest_red_emergency(auth_headers):
    payload = {"sender": "guest456", "content": "HELP! I am stranded on the beach and it is dangerous."}
    response = client.post("/exmail/ingest?channel=sms", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["ai_action"] == "LOCKED"
    assert data["priority"] == "P1"

def test_escalation_logic(auth_headers):
    # Ingest a P1 message
    client.post("/exmail/ingest?channel=sms",
                json={"sender": "vip_guest", "content": "Emergency! System down."},
                headers=auth_headers)

    # Trigger escalation check
    response = client.post("/exmail/escalation/check", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "ESCALATION_CHECK_TRIGGERED"

    # Verify SHADOW log for escalation
    events = [b["event_type"] for b in shadow_core.chain]
    assert "escalation.triggered" in events

def test_iluvia_execution_confirm(auth_headers):
    order_id = "ORD-TEST-99"
    signal = {"type": "QR_SCAN", "valid": True}

    response = client.post(f"/bubble/execution/confirm?order_id={order_id}", json=signal, headers=auth_headers)
    assert response.status_code == 200
    assert response.json() is True

    # Verify reality check in SHADOW
    events = [b["event_type"] for b in shadow_core.chain]
    assert "execution.confirmed" in events

def test_iluvia_execution_mismatch(auth_headers):
    order_id = "ORD-TEST-100"
    # Procurement order (default) expects QR_SCAN or WAREHOUSE_INTAKE, not GPS
    signal = {"type": "GPS_GEOFENCE", "valid": True}

    response = client.post(f"/bubble/execution/confirm?order_id={order_id}", json=signal, headers=auth_headers)
    assert response.status_code == 500
    assert "REALITY MISMATCH" in response.json()["detail"]

    # Verify failure rollback log in SHADOW
    events = [b["event_type"] for b in shadow_core.chain]
    assert "bubble.execution.confirm.failed" in events

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from modules.retail.autonomous.api.session import router as session_router
from modules.retail.autonomous.api.cart import router as cart_router
from modules.retail.autonomous.api.exit import router as exit_router
from modules.retail.autonomous.api.admin import router as admin_router
from modules.retail.autonomous.models.database import init_db, Base, engine, SessionLocal, RetailHardwareNode
import uuid
from datetime import datetime, timezone

# Initialize DB for tests
init_db()

app = FastAPI()
app.include_router(session_router, prefix="/api/v1/retail/autonomous")
app.include_router(cart_router, prefix="/api/v1/retail/autonomous")
app.include_router(exit_router, prefix="/api/v1/retail/autonomous")
app.include_router(admin_router, prefix="/api/v1/retail/autonomous")

client = TestClient(app)

MOCK_HEADERS = {
    "X-Signature": "mock_sig",
    "X-Timestamp": "1234567890",
    "X-Request-Id": "mock_req_id"
}

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Setup trusted hardware
    db = SessionLocal()
    node = RetailHardwareNode(
        node_identifier="VISION",
        node_type="CAMERA",
        status="ONLINE",
        trust_score=1.0
    )
    db.add(node)
    node2 = RetailHardwareNode(
        node_identifier="SHELF",
        node_type="SHELF",
        status="ONLINE",
        trust_score=1.0
    )
    db.add(node2)
    db.commit()
    db.close()

def test_session_start_success():
    response = client.post("/api/v1/retail/autonomous/session/start", json={
        "store_id": "STORE_001",
        "auth_type": "NFC",
        "auth_token": "valid_token"
    }, headers=MOCK_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["status"] == "OPEN"
    assert data["unlock"] is True

def test_session_start_invalid_token():
    response = client.post("/api/v1/retail/autonomous/session/start", json={
        "store_id": "STORE_001",
        "auth_type": "NFC",
        "auth_token": "invalid_token"
    }, headers=MOCK_HEADERS)
    assert response.status_code == 401

def test_cart_workflow_pick_put():
    # 1. Start session
    resp = client.post("/api/v1/retail/autonomous/session/start", json={
        "store_id": "STORE_001",
        "auth_type": "NFC",
        "auth_token": "valid_token"
    }, headers=MOCK_HEADERS)
    session_id = resp.json()["session_id"]

    # PICK an item
    client.post("/api/v1/retail/autonomous/sensor/event", json={
        "session_id": session_id,
        "event_type": "PICK",
        "source": "VISION",
        "product_id": "SKU_123",
        "qty": 2,
        "confidence": 0.98,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }, headers=MOCK_HEADERS)

    # Get Cart
    response = client.get(f"/api/v1/retail/autonomous/session/{session_id}/cart", headers=MOCK_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == "SKU_123"
    assert float(data["items"][0]["qty"]) == 2.0
    assert float(data["running_total"]) == 10.0

    # PUT one back
    client.post("/api/v1/retail/autonomous/sensor/event", json={
        "session_id": session_id,
        "event_type": "PUT",
        "source": "SHELF",
        "product_id": "SKU_123",
        "qty": 1,
        "confidence": 0.99,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }, headers=MOCK_HEADERS)

    response = client.get(f"/api/v1/retail/autonomous/session/{session_id}/cart", headers=MOCK_HEADERS)
    assert float(response.json()["items"][0]["qty"]) == 1.0

def test_exit_auto_settle_high_confidence():
    # 1. Start session
    resp = client.post("/api/v1/retail/autonomous/session/start", json={
        "store_id": "STORE_001",
        "auth_type": "NFC",
        "auth_token": "valid_token"
    }, headers=MOCK_HEADERS)
    session_id = resp.json()["session_id"]

    client.post("/api/v1/retail/autonomous/sensor/event", json={
        "session_id": session_id,
        "event_type": "PICK",
        "source": "VISION",
        "product_id": "SKU_123",
        "qty": 1,
        "confidence": 0.97,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }, headers=MOCK_HEADERS)

    response = client.post("/api/v1/retail/autonomous/session/exit", json={"session_id": session_id}, headers=MOCK_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SETTLED"
    assert "settlement_id" in data
    assert data["receipt_id"].startswith("INV-")

def test_exit_flagged_low_confidence():
    # 1. Start session
    resp = client.post("/api/v1/retail/autonomous/session/start", json={
        "store_id": "STORE_001",
        "auth_type": "NFC",
        "auth_token": "valid_token"
    }, headers=MOCK_HEADERS)
    session_id = resp.json()["session_id"]

    client.post("/api/v1/retail/autonomous/sensor/event", json={
        "session_id": session_id,
        "event_type": "PICK",
        "source": "VISION",
        "product_id": "SKU_123",
        "qty": 1,
        "confidence": 0.92, # Below 0.95 auto-settle threshold
        "timestamp": datetime.now(timezone.utc).isoformat()
    }, headers=MOCK_HEADERS)

    response = client.post("/api/v1/retail/autonomous/session/exit", json={"session_id": session_id}, headers=MOCK_HEADERS)
    assert response.status_code == 200
    assert response.json()["status"] == "FLAGGED"

def test_admin_resolve_approve():
    # 1. Start session
    resp = client.post("/api/v1/retail/autonomous/session/start", json={
        "store_id": "STORE_001",
        "auth_type": "NFC",
        "auth_token": "valid_token"
    }, headers=MOCK_HEADERS)
    session_id = resp.json()["session_id"]

    # 2. Add item to cart
    client.post("/api/v1/retail/autonomous/sensor/event", json={
        "session_id": session_id,
        "event_type": "PICK",
        "source": "VISION",
        "product_id": "SKU_999",
        "qty": 1,
        "confidence": 0.91,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }, headers=MOCK_HEADERS)

    response = client.post("/api/v1/retail/autonomous/review/resolve", json={
        "session_id": session_id,
        "action": "APPROVE",
        "reason": "Staff verified items",
        "reviewer_token": "staff_token"
    }, headers=MOCK_HEADERS)
    assert response.status_code == 200
    assert response.json()["status"] == "SETTLED"

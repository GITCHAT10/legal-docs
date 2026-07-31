import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from modules.retail.autonomous.api.session import router as session_router
from modules.retail.autonomous.api.cart import router as cart_router
from modules.retail.autonomous.api.exit import router as exit_router
from modules.retail.autonomous.api.admin import router as admin_router
from modules.retail.autonomous.models.database import init_db, Base, engine, RetailSession
import uuid
from datetime import datetime, timezone
import concurrent.futures

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
    from modules.retail.autonomous.models.database import SessionLocal, RetailHardwareNode
    db = SessionLocal()
    node = RetailHardwareNode(
        node_identifier="CAM_01",
        node_type="CAMERA",
        status="ONLINE",
        trust_score=1.0
    )
    db.add(node)
    db.commit()
    db.close()

def test_idempotent_exit():
    # 1. Start session
    resp = client.post("/api/v1/retail/autonomous/session/start", json={
        "store_id": "STORE_001",
        "auth_type": "NFC",
        "auth_token": "valid_token"
    }, headers=MOCK_HEADERS)
    session_id = resp.json()["session_id"]

    # 2. Add high-confidence item
    client.post("/api/v1/retail/autonomous/sensor/event", json={
        "session_id": session_id,
        "event_type": "PICK",
        "source": "CAM_01",
        "product_id": "SKU_123",
        "qty": 1,
        "confidence": 0.99,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }, headers=MOCK_HEADERS)

    # 3. Exit first time
    resp1 = client.post("/api/v1/retail/autonomous/session/exit", json={"session_id": session_id}, headers=MOCK_HEADERS)
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "SETTLED"
    settlement_id = resp1.json()["settlement_id"]

    # 4. Exit second time (Idempotent)
    resp2 = client.post("/api/v1/retail/autonomous/session/exit", json={"session_id": session_id}, headers=MOCK_HEADERS)
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "SETTLED"
    assert resp2.json()["settlement_id"] == settlement_id
    assert "already processed" in resp2.json()["message"]

def test_security_missing_headers():
    response = client.post("/api/v1/retail/autonomous/session/start", json={
        "store_id": "STORE_001",
        "auth_type": "NFC",
        "auth_token": "valid_token"
    })
    # FastAPI returns 422 for missing required headers defined as Header(...)
    assert response.status_code == 422

def test_anomaly_detection_impossible_put():
    # 1. Start session
    resp = client.post("/api/v1/retail/autonomous/session/start", json={
        "store_id": "STORE_001",
        "auth_type": "NFC",
        "auth_token": "valid_token"
    }, headers=MOCK_HEADERS)
    session_id = resp.json()["session_id"]

    # 2. PICK then PUT more than PICKed
    client.post("/api/v1/retail/autonomous/sensor/event", json={
        "session_id": session_id,
        "event_type": "PICK",
        "source": "CAM_01",
        "product_id": "SKU_123",
        "qty": 1,
        "confidence": 0.99,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }, headers=MOCK_HEADERS)

    client.post("/api/v1/retail/autonomous/sensor/event", json={
        "session_id": session_id,
        "event_type": "PUT",
        "source": "CAM_01",
        "product_id": "SKU_123",
        "qty": 2, # More than PICKed
        "confidence": 0.99,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }, headers=MOCK_HEADERS)

    # 3. Exit
    resp = client.post("/api/v1/retail/autonomous/session/exit", json={"session_id": session_id}, headers=MOCK_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"] == "FLAGGED"

def test_admin_reversal():
    # 1. Settled session
    resp = client.post("/api/v1/retail/autonomous/session/start", json={
        "store_id": "STORE_001",
        "auth_type": "NFC",
        "auth_token": "valid_token"
    }, headers=MOCK_HEADERS)
    session_id = resp.json()["session_id"]

    client.post("/api/v1/retail/autonomous/sensor/event", json={
        "session_id": session_id,
        "event_type": "PICK",
        "source": "CAM_01",
        "product_id": "SKU_123",
        "qty": 1,
        "confidence": 0.99,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }, headers=MOCK_HEADERS)

    client.post("/api/v1/retail/autonomous/session/exit", json={"session_id": session_id}, headers=MOCK_HEADERS)

    # 2. Reverse it
    resp = client.post("/api/v1/retail/autonomous/review/resolve", json={
        "session_id": session_id,
        "action": "REVERSE",
        "reason": "Customer complained",
        "reviewer_token": "supervisor_token"
    }, headers=MOCK_HEADERS)

    assert resp.status_code == 200
    assert resp.json()["status"] == "REVERSED"

def test_evidence_integrity():
    # 1. Complete a session
    resp = client.post("/api/v1/retail/autonomous/session/start", json={
        "store_id": "STORE_001",
        "auth_type": "NFC",
        "auth_token": "valid_token"
    }, headers=MOCK_HEADERS)
    session_id = resp.json()["session_id"]

    client.post("/api/v1/retail/autonomous/sensor/event", json={
        "session_id": session_id,
        "event_type": "PICK",
        "source": "CAM_01",
        "product_id": "SKU_123",
        "qty": 1,
        "confidence": 0.99,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }, headers=MOCK_HEADERS)

    client.post("/api/v1/retail/autonomous/session/exit", json={"session_id": session_id}, headers=MOCK_HEADERS)

    # 2. Verify evidence in DB
    from modules.retail.autonomous.models.database import SessionLocal
    db = SessionLocal()
    session = db.query(RetailSession).filter(RetailSession.id == uuid.UUID(session_id)).first()
    assert session.evidence_bundle is not None
    assert "integrity_checksum" in session.evidence_bundle
    assert len(session.evidence_bundle["sensor_evidence"]["event_timeline"]) == 1
    db.close()

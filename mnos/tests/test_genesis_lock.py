import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import uuid
from datetime import date

from mnos.interfaces.prestige.main import app
from mnos.core.db.base_class import Base
from mnos.core.api.deps import get_db
from mnos.core.aegis.security.security import get_password_hash
from mnos.core.models.user import User

# Mock DB for Genesis Verification
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_genesis_lock.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    user = User(email="genesis@mnos.com", hashed_password=get_password_hash("genesis"), is_superuser=True, full_name="Genesis")
    db.add(user)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def get_auth_header(patente: str = "MIG-GENESIS-01"):
    response = client.post("/api/v1/login/access-token", data={"username": "genesis@mnos.com", "password": "genesis"})
    token = response.json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
        "X-NexGen-Patente": patente
    }

def test_genesis_locked_booking_flow():
    headers = get_auth_header()

    # 1. Start with invalid patente (Should FAIL with 401)
    bad_headers = get_auth_header(patente="STOLEN-IDENTITY")
    res = client.post("/api/v1/reservations/rooms", json={
        "room_number": "G1", "room_type": "Villa", "trace_id": "T1", "tenant_id": "default"
    }, headers=bad_headers)
    assert res.status_code == 401

    # 2. Valid Sovereign Flow: Create Room
    room_trace = f"ROOM-{uuid.uuid4().hex[:8]}"
    res = client.post("/api/v1/reservations/rooms", json={
        "room_number": "GEN1", "room_type": "Water Villa", "trace_id": room_trace, "tenant_id": "default"
    }, headers=headers)
    assert res.status_code == 200
    room_id = res.json()["id"]

    # 3. Create Reservation (Should auto-open folio)
    res_trace = f"RES-{uuid.uuid4().hex[:8]}"
    res = client.post("/api/v1/reservations/", json={
        "guest_id": 1, "trace_id": res_trace, "tenant_id": "default",
        "stays": [{"room_id": room_id, "check_in_date": str(date.today()), "check_out_date": str(date.today())}]
    }, headers=headers)
    assert res.status_code == 200
    reservation_id = res.json()["id"]

    # 4. Verify Folio was auto-opened via SDK
    folio_res = client.get("/api/v1/finance/summary", headers=headers)
    assert folio_res.status_code == 200

    # 5. Post Sovereign Charge (Locked in SHADOW)
    charge_trace = f"CH-{uuid.uuid4().hex[:8]}"
    res = client.post(f"/api/v1/finance/folios/1/charges", json={
        "trace_id": charge_trace, "type": "room", "base_amount": 1000.0, "tenant_id": "default"
    }, headers=headers)
    assert res.status_code == 200

    # 6. Verify SHADOW evidence chaining
    from mnos.core.shadow.models import Evidence
    db = TestingSessionLocal()
    # Find evidence for the charge
    evidence = db.query(Evidence).filter(Evidence.trace_id == charge_trace).first()
    assert evidence is not None
    assert evidence.actor == "genesis@mnos.com"
    assert evidence.current_hash is not None

def test_genesis_fail_closed_shadow():
    headers = get_auth_header()

    # Missing trace_id should be blocked by validation (ValueError in service)
    # FastAPI returns 500 for unhandled ValueError in endpoint
    res = client.post(f"/api/v1/finance/folios/1/charges", json={
        "trace_id": "", "type": "room", "base_amount": 1000.0, "tenant_id": "default"
    }, headers=headers)
    assert res.status_code >= 400

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime, UTC

from mnos.interfaces.prestige.main import app
from mnos.core.db.base_class import Base
from mnos.core.api.deps import get_db
from mnos.core.security.security import get_password_hash
from mnos.core.models.user import User

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_united_transfer.db"
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

def get_auth_header():
    response = client.post("/api/v1/login/access-token", data={"username": "genesis@mnos.com", "password": "genesis"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "X-NexGen-Patente": "MIG-GENESIS-01"}

def test_multi_leg_booking():
    headers = get_auth_header()
    trace_id = f"UT-{uuid.uuid4().hex[:8]}"

    res = client.post("/api/v1/united-transfer/bookings", json={
        "trace_id": trace_id,
        "external_reference": "TA-12345",
        "legs": [
            {"type": "land", "origin": "Male Airport", "destination": "TMA Terminal"},
            {"type": "air", "origin": "TMA Terminal", "destination": "Resort Island Jetty"}
        ]
    }, headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert data["trace_id"] == trace_id
    assert data["external_reference"] == "TA-12345"

def test_availability_query():
    headers = get_auth_header()
    res = client.get("/api/v1/united-transfer/availability", params={
        "origin": "MLE",
        "destination": "RESORT",
        "departure_date": datetime.now(UTC).isoformat()
    }, headers=headers)

    assert res.status_code == 200
    assert len(res.json()) > 0

def test_telemetry_and_payout():
    headers = get_auth_header()
    # 1. Report telemetry
    res = client.post("/api/v1/united-transfer/telemetry", json={
        "leg_id": 1,
        "latitude": 4.1755,
        "longitude": 73.5093,
        "speed": 10.5
    }, headers=headers)
    assert res.status_code == 200

    # 2. Verify instant payout logic (internal check)
    from mnos.modules.united_transfer.services import handshake_service
    db = TestingSessionLocal()
    # Manual verification of payout logic since we don't have an endpoint yet for wallet
    handshake_service.verify_dual_qr(db, leg_id=1, scan_data="QR-INVALID", actor="test")
    # This shouldn't crash

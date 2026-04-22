import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime, UTC
from unittest.mock import AsyncMock, patch

from mnos.interfaces.prestige.main import app
from mnos.core.db.base_class import Base
from united_transfer_system.db_session import get_ut_db
from mnos.core.security.security import get_password_hash
from mnos.core.models.user import User

# STANDALONE DB FOR TEST
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_united_transfer.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_ut_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_ut_db] = override_get_ut_db
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def get_auth_header():
    return {
        "Authorization": "Bearer fake-token",
        "X-NexGen-Patente": "MIG-GENESIS-01",
        "X-UT-Timestamp": str(datetime.now(UTC).timestamp()),
        "X-UT-Partner-Key": "test-partner",
        "X-UT-Signature": "fake-sig"
    }

@patch("united_transfer_system.api.router.nexus_client")
def test_multi_leg_booking(mock_nexus):
    # Mock NEXUS interactions
    mock_nexus.verify_session = AsyncMock(return_value=True)
    mock_nexus.preauthorize_payment = AsyncMock(return_value=True)
    mock_nexus.commit_evidence = AsyncMock(return_value=True)
    mock_nexus.publish_event = AsyncMock(return_value=True)

    headers = get_auth_header()
    trace_id = f"UT-{uuid.uuid4().hex[:8]}"

    res = client.post("/api/v1/united-transfer/v1/book", json={
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

@patch("united_transfer_system.api.router.nexus_client")
def test_availability_query(mock_nexus):
    mock_nexus.verify_session = AsyncMock(return_value=True)

    headers = get_auth_header()
    res = client.get("/api/v1/united-transfer/v1/availability", params={
        "origin": "MLE",
        "destination": "RESORT",
        "departure_date": datetime.now(UTC).isoformat()
    }, headers=headers)

    assert res.status_code == 200
    assert len(res.json()) > 0

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime, UTC
from unittest.mock import AsyncMock, patch, MagicMock

from mnos.interfaces.prestige.main import app
from mnos.core.db.base_class import Base
from united_transfer_system.db_session import get_ut_db
from united_transfer_system import models, schemas
from united_transfer_system.services import booking_service

# STANDALONE DB FOR TEST
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_sovereign_mobility.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_ut_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_ut_db] = override_get_ut_db
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # No drop_all here to avoid "database is locked" during cleanup if any session is lingering
    # SQLite in-memory or a fresh file is better for CI

def get_sovereign_headers(aegis_id="OPERATOR-01", device_id="DEVICE-X"):
    return {
        "Authorization": "Bearer fake-token",
        "X-NexGen-Patente": "MIG-GENESIS-01",
        "X-AEGIS-ID": aegis_id,
        "X-Device-ID": device_id,
        "X-UT-Signature": "SOVEREIGN-SIG",
        "X-UT-Trace-ID": f"TR-{uuid.uuid4().hex[:8]}",
        "X-UT-Timestamp": str(datetime.now(UTC).timestamp())
    }

def test_missing_trace_id_rejected():
    headers = get_sovereign_headers()
    # Attempt booking without trace_id in JSON (enforced by pydantic)
    res = client.post("/api/v1/united-transfer/v1/book", json={
        "external_reference": "TA-1",
        "legs": []
    }, headers=headers)
    assert res.status_code == 422

def test_invalid_state_transition_rejected():
    db = TestingSessionLocal()
    headers = get_sovereign_headers()

    # 1. Create Journey
    trace_id = f"TR-{uuid.uuid4().hex[:8]}"
    res = client.post("/api/v1/united-transfer/v1/book", json={
        "trace_id": trace_id,
        "legs": [{"type": "land", "origin": "A", "destination": "B"}]
    }, headers=headers)
    assert res.status_code == 200
    journey_id = res.json()["id"]

    # 2. Try to skip to COMPLETED from CREATED
    # ExecutionGuard will catch the ValueError and raise 500 HTTPException
    ctx = {"trace_id": "T1", "aegis_id": "OP"}
    with pytest.raises(HTTPException) as excinfo:
        booking_service.update_journey_status(db, journey_id, models.JourneyStatus.COMPLETED, ctx)
    assert excinfo.value.status_code == 500
    db.close()

def test_payment_blocked_without_qr2():
    db = TestingSessionLocal()
    headers = get_sovereign_headers()

    # Create a journey
    trace_id = f"TR-{uuid.uuid4().hex[:8]}"
    res = client.post("/api/v1/united-transfer/v1/book", json={
        "trace_id": trace_id,
        "legs": [{"type": "land", "origin": "A", "destination": "B"}]
    }, headers=headers)
    assert res.status_code == 200
    journey_id = res.json()["id"]

    # Try to pay immediately
    ctx = {"trace_id": "T2", "aegis_id": "FIN"}
    import asyncio
    with pytest.raises(HTTPException):
        # Even if run_until_complete, it's wrapped in guard -> 500
        loop = asyncio.new_event_loop()
        loop.run_until_complete(booking_service.release_payment(db, journey_id, ctx))
    db.close()

def test_unsigned_context_rejected():
    # No headers at all -> FastAPI returns 422 for missing required Header(...)
    res = client.get("/api/v1/united-transfer/v1/availability")
    assert res.status_code == 422

@patch("united_transfer_system.services.booking_service.nexus_client")
def test_sync_buffer_durability(mock_nexus):
    from mnos.core.db.sync_buffer import SyncBuffer
    buffer = SyncBuffer()

    buffer.queue_transaction("SYNC-1", {"data": "mobility"})

    # Mock DB commit failure
    mock_db = MagicMock()
    mock_db.commit.side_effect = Exception("DB DEAD")

    with pytest.raises(Exception):
        buffer.process_sync(mock_db)

    # Buffer MUST NOT be cleared if commit fails
    assert len(buffer._buffer) == 1

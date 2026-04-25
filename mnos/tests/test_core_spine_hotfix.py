import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime, UTC, date
from unittest.mock import MagicMock

from mnos.interfaces.prestige.main import app
from mnos.core.db.base_class import Base
from mnos.core.api.deps import get_db
from mnos.core.security.security import get_password_hash
from mnos.core.models.user import User
from mnos.modules.fce import models as fce_models, service as fce_service
from mnos.modules.maintain import service as maintain_service, enums as maintain_enums
from mnos.interfaces.prestige.guests import models as guest_models
from mnos.core.db.sync_buffer import SyncBuffer
from mnos.modules.inn.reservations import service as inn_service, schemas as inn_schemas, models as inn_models

# Mock DB for Genesis Verification
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_core_spine.db"
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
    user = User(email="hotfix@mnos.com", hashed_password=get_password_hash("hotfix"), is_superuser=True, full_name="Hotfix")
    db.add(user)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def get_auth_header():
    response = client.post("/api/v1/login/access-token", data={"username": "hotfix@mnos.com", "password": "hotfix"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "X-NexGen-Patente": "MIG-HOTFIX-01"}

def test_fce_finalize_invoice():
    db = TestingSessionLocal()
    headers = get_auth_header()

    # 1. Create Folio
    folio = fce_models.Folio(trace_id="T1", external_reservation_id="R1")
    db.add(folio)
    db.commit()

    # 2. Call finalize
    res = client.post(f"/api/v1/finance/folios/{folio.id}/finalize?trace_id=TF1", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "finalized"

    # 3. Idempotency check
    res2 = client.post(f"/api/v1/finance/folios/{folio.id}/finalize?trace_id=TF2", headers=headers)
    assert res2.status_code == 200
    assert res2.json()["invoice_number"] == res.json()["invoice_number"]

def test_maintenance_trace_id():
    db = TestingSessionLocal()
    # 1. Create Room (pre-req)
    room = inn_models.Room(room_number="101", room_type="Standard", trace_id="RT1")
    db.add(room)
    db.commit()

    # 2. Create Ticket
    ticket = maintain_service.create_ticket(db, room_id=room.id, title="Leak", description="Faucet", priority=maintain_enums.TicketPriority.P3)
    assert ticket.trace_id is not None
    assert ticket.trace_id.startswith("MAINT-CREATE-")

def test_prestige_guest_trace_id():
    headers = get_auth_header()
    res = client.post("/api/v1/guests/", json={
        "first_name": "John", "last_name": "Doe", "email": f"john{uuid.uuid4().hex}@doe.com", "phone": "123"
    }, headers=headers)
    assert res.status_code == 200
    assert res.json()["trace_id"] is not None
    assert res.json()["trace_id"].startswith("GUEST-CREATE-")

def test_sync_buffer_durability():
    buffer = SyncBuffer()
    db = TestingSessionLocal()
    buffer.queue_transaction("TS1", {"data": "test"})

    # Simulate commit failure
    mock_db = MagicMock()
    mock_db.commit.side_effect = Exception("Commit Failed")

    with pytest.raises(Exception):
        buffer.process_sync(mock_db)

    # Buffer should NOT be cleared if commit fails
    assert len(buffer._buffer) == 1

def test_reservation_automation_event():
    db = TestingSessionLocal()
    # Mock event dispatcher
    from mnos.core.events.dispatcher import event_dispatcher
    event_dispatcher.dispatch = MagicMock()

    room = inn_models.Room(room_number="202", room_type="Suite", trace_id="RT2", capacity=5)
    db.add(room)
    db.commit()

    res_in = inn_schemas.ReservationCreate(
        guest_id=1, trace_id=f"T-RES-{uuid.uuid4().hex[:8]}", stays=[{"room_id": room.id, "check_in_date": str(date.today()), "check_out_date": str(date.today())}]
    )
    inn_service.create_reservation(db, reservation_in=res_in)

    # Verify reservation_confirmed was dispatched
    # It's called twice (once for confirmed, once for created as per bridge)
    calls = [call.args[0] for call in event_dispatcher.dispatch.call_args_list]
    assert "reservation_confirmed" in calls

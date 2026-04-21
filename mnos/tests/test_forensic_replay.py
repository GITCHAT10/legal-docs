import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import uuid
from datetime import date
from unittest.mock import patch

from mnos.interfaces.prestige.main import app
from mnos.core.db.base_class import Base
from mnos.core.api.deps import get_db
from mnos.core.security.security import get_password_hash
from mnos.core.models.user import User

# Mock DB for Forensic Replay
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_forensic.db"
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
    user = User(email="forensic@mnos.com", hashed_password=get_password_hash("forensic"), is_superuser=True, full_name="Forensic Admin")
    db.add(user)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def get_auth_header():
    response = client.post("/api/v1/login/access-token", data={"username": "forensic@mnos.com", "password": "forensic"})
    return {"Authorization": f"Bearer {response.json()['access_token']}", "X-NexGen-Patente": "MIG-FORENSIC-01"}

def test_failure_scenario_broken_shadow():
    headers = get_auth_header()

    # 1. Mock SHADOW failure
    with patch("mnos.modules.shadow.service.commit_evidence", side_effect=RuntimeError("SHADOW_DB_FAILURE")):
        res = client.post("/api/v1/finance/folios", json={
            "external_reservation_id": "RES-FAIL",
            "trace_id": f"TR-{uuid.uuid4().hex[:8]}"
        }, headers=headers)

        # 2. Verify Fail-Closed (500 error due to RuntimeError in service)
        assert res.status_code == 500

        # 3. Verify no data in FCE (Atomic Rollback)
        db = TestingSessionLocal()
        from mnos.modules.fce.models import Folio
        folio = db.query(Folio).filter(Folio.external_reservation_id == "RES-FAIL").first()
        assert folio is None

def test_forensic_replay_flow():
    headers = get_auth_header()

    # 1. Perform multiple operations on an entity
    folio_trace = f"TR-{uuid.uuid4().hex[:8]}"
    res = client.post("/api/v1/finance/folios", json={
        "external_reservation_id": "RES-REPLAY",
        "trace_id": folio_trace
    }, headers=headers)
    folio_id = res.json()["id"]

    # 2. Post Charge
    client.post(f"/api/v1/finance/folios/{folio_id}/charges", json={
        "trace_id": f"CH-{uuid.uuid4().hex[:8]}", "type": "room", "base_amount": 500.0
    }, headers=headers)

    # 3. Finalize
    client.post(f"/api/v1/finance/folios/{folio_id}/finalize", headers=headers)

    # 4. Replay history from SHADOW
    replay_res = client.get(f"/api/v1/shadow/replay/FOLIO/{folio_id}", headers=headers)
    assert replay_res.status_code == 200
    history = replay_res.json()["history"]

    # Verify events in sequence
    assert len(history) >= 1
    assert history[0]["action"] == "OPEN_FOLIO"

    # Verify Chain Integrity
    verify_res = client.get("/api/v1/shadow/verify", headers=headers)
    assert verify_res.json()["verified"] is True

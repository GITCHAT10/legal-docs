import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime
import os
import uuid
from unittest.mock import patch

from mnos.interfaces.prestige.main import app
from mnos.core.db.base_class import Base
from mnos.core.api.deps import get_db
from mnos.core.security.security import get_password_hash
from mnos.core.models.user import User

# Mock DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_sovereign_replays.db"
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
    user = User(email="sov@mnos.com", hashed_password=get_password_hash("sov"), is_superuser=True, full_name="Sov Admin")
    db.add(user)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def get_auth_header():
    response = client.post("/api/v1/login/access-token", data={"username": "sov@mnos.com", "password": "sov"})
    return {"Authorization": f"Bearer {response.json()['access_token']}", "X-NexGen-Patente": "MIG-SOV-01"}

def test_tax_transition_july_2025():
    """Verify TGST rate transition (16% -> 17%) around July 2025."""
    headers = get_auth_header()

    # Pre-2025-07-01: 16% TGST
    res_june = client.post("/api/v1/finance/folios/1/charges", json={
        "trace_id": f"CH-{uuid.uuid4().hex[:4]}", "type": "room", "base_amount": 1000.0,
        "business_date": "2025-06-30"
    }, headers=headers)
    # 1000 + 10%(100) = 1100. 1100 * 0.16 = 176. Total 1276.0
    assert res_june.json()["amount"] == 1276.0

    # Post-2025-07-01: 17% TGST
    res_july = client.post("/api/v1/finance/folios/1/charges", json={
        "trace_id": f"CH-{uuid.uuid4().hex[:4]}", "type": "room", "base_amount": 1000.0,
        "business_date": "2025-07-01"
    }, headers=headers)
    # 1000 + 10%(100) = 1100. 1100 * 0.17 = 187. Total 1287.0
    assert res_july.json()["amount"] == 1287.0

def test_green_tax_transition_jan_2025():
    """Verify Green Tax rate transition ($6 -> $12) around Jan 2025."""
    headers = get_auth_header()

    # Pre-2025-01-01: $6
    res_dec = client.post("/api/v1/finance/folios/1/charges", json={
        "trace_id": f"CH-{uuid.uuid4().hex[:4]}", "type": "room", "base_amount": 1000.0,
        "business_date": "2024-12-31", "apply_green_tax": True, "nights": 1
    }, headers=headers)
    # Base 1000 + SC 100 + TGST 176 (16% in 2024) + Green 6 = 1282.0
    assert res_dec.json()["amount"] == 1282.0

    # Post-2025-01-01: $12
    res_jan = client.post("/api/v1/finance/folios/1/charges", json={
        "trace_id": f"CH-{uuid.uuid4().hex[:4]}", "type": "room", "base_amount": 1000.0,
        "business_date": "2025-01-01", "apply_green_tax": True, "nights": 1
    }, headers=headers)
    # Base 1000 + SC 100 + TGST 176 (16% in Jan 2025) + Green 12 = 1288.0
    assert res_jan.json()["amount"] == 1288.0

def test_fail_closed_shadow_tamper():
    """Failure Scenario: SHADOW failure blocks FCE mutation."""
    headers = get_auth_header()

    with patch("mnos.modules.shadow.service.commit_evidence", side_effect=RuntimeError("BYZANTINE_FAULT")):
        res = client.post("/api/v1/finance/folios", json={
            "external_reservation_id": "INVESTOR-DEMO",
            "trace_id": f"TR-{uuid.uuid4().hex[:4]}"
        }, headers=headers)

        # Genesis Lock must trigger 500/Fail-Stop
        assert res.status_code == 500

        # Verify FCE state is clean (No record created due to rollback)
        db = TestingSessionLocal()
        from mnos.modules.fce.models import Folio
        f = db.query(Folio).filter(Folio.external_reservation_id == "INVESTOR-DEMO").first()
        assert f is None

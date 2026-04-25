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
from mnos.core.security.security import get_password_hash
from mnos.core.models.user import User
from mnos.core.security.aegis_state import set_system_state, SystemState

# Mock DB for Stress Test
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_stress.db"
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
    user = User(email="stress@mnos.com", hashed_password=get_password_hash("stress"), is_superuser=True, full_name="Stress User")
    db.add(user)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def get_auth_header():
    response = client.post("/api/v1/login/access-token", data={"username": "stress@mnos.com", "password": "stress"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "X-NexGen-Patente": "MIG-STRESS-01"}

def test_broken_bundle_stress_flow():
    """
    Stress Test: Simulation of a broken bundle under Protection Mode.
    1. Activate Protection Mode (AEGIS State Lock).
    2. Verify Premium charges are throttled/discounted.
    3. Perform Bundle Split (Integrity Engine).
    4. Verify SHADOW evidence chaining.
    """
    headers = get_auth_header()
    db = TestingSessionLocal()

    # 1. Activate PROTECTION_MODE
    set_system_state(db, SystemState.PROTECTED, "stress@mnos.com", "System Stress Event")

    # 2. Open Folio
    folio_trace = f"STRESS-FOL-{uuid.uuid4().hex[:4]}"
    res = client.post("/api/v1/finance/folios", json={
        "external_reservation_id": "STRESS-RES-01",
        "trace_id": folio_trace
    }, headers=headers)
    folio_id = res.json()["id"]

    # 3. Post Premium Charge (Should be discounted in Protection Mode)
    # Service layer logic: premium_room discounted by 50%
    charge_trace = f"STRESS-CH-{uuid.uuid4().hex[:4]}"
    res = client.post(f"/api/v1/finance/folios/{folio_id}/charges", json={
        "trace_id": charge_trace,
        "type": "premium_room",
        "base_amount": 2000.0
    }, headers=headers)

    # Calculation: Base 2000 -> 1000 (Protection Mode). 1000 + 10%(100) + 16%(176) = 1276.0
    # Current test date is pre-July 2025, so 16% TGST applies
    assert res.json()["base_amount"] == 1000.0
    assert res.json()["amount"] == 1276.0

    # 4. Bundle Split Simulation
    from mnos.modules.fce.bundle_integrity import split_bundle_contract
    line_id = res.json()["id"]
    split_trace = f"STRESS-SPLIT-{uuid.uuid4().hex[:4]}"
    target_res_id = "STRESS-RES-WALKED"

    target_folio = split_bundle_contract(db, folio_id, [line_id], target_res_id, split_trace, "stress@mnos.com")
    assert target_folio.external_reservation_id == target_res_id
    assert target_folio.total_amount == 1276.0

    # 5. Verify Audit Chain (SHADOW)
    from mnos.modules.shadow.models import Evidence
    evidences = db.query(Evidence).filter(Evidence.trace_id.like("STRESS-%")).all()
    assert len(evidences) >= 3 # Folio Open, Charge Post, Bundle Move

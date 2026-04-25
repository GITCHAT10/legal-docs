import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime
import os
import uuid

from mnos.interfaces.prestige.main import app
from mnos.core.db.base_class import Base
from mnos.core.api.deps import get_db
from mnos.core.security.security import get_password_hash
from mnos.core.models.user import User

# Mock DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_mnos_sovereign.db"
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
    # Create a superuser
    user = User(
        email="admin@mnos.com",
        hashed_password=get_password_hash("admin"),
        is_superuser=True,
        full_name="Admin"
    )
    db.add(user)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def get_auth_header():
    response = client.post(
        "/api/v1/login/access-token",
        data={"username": "admin@mnos.com", "password": "admin"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_mnos_sovereign_flow():
    os.environ["TESTING"] = "1"
    headers = get_auth_header()

    # 1. Pre-req: Guest and Room
    guest_trace = f"GUEST-{uuid.uuid4().hex[:8]}"
    guest_res = client.post("/api/v1/guests/", json={
        "first_name": "Sovereign",
        "last_name": "User",
        "email": "sov@mnos.com",
        "trace_id": guest_trace
    }, headers=headers)
    assert guest_res.status_code == 200
    guest_id = guest_res.json()["id"]

    room_trace = f"ROOM-{uuid.uuid4().hex[:8]}"
    room_res = client.post("/api/v1/inn/reservations/rooms", json={
        "room_number": "SOV1",
        "room_type": "Overwater Villa",
        "trace_id": room_trace
    }, headers=headers)
    assert room_res.status_code == 200
    room_id = room_res.json()["id"]

    # 2. RESERVATION (INN)
    res_trace = f"RES-{uuid.uuid4().hex[:8]}"
    reservation_data = {
        "guest_id": guest_id,
        "total_amount": 0.0,
        "trace_id": res_trace,
        "stays": [{"room_id": room_id, "check_in_date": str(date.today()), "check_out_date": str(date.today())}]
    }
    res = client.post("/api/v1/inn/reservations/", json=reservation_data, headers=headers)
    assert res.status_code == 200
    reservation_id = res.json()["id"]

    # 3. TRANSFER (AQUA)
    trans_trace = f"TRANS-{uuid.uuid4().hex[:8]}"
    transfer_data = {
        "external_reservation_id": str(reservation_id),
        "type": "boat",
        "pickup_location": "Airport",
        "destination": "Sovereign Island",
        "trace_id": trans_trace
    }
    res = client.post("/api/v1/transfers/", json=transfer_data, headers=headers)
    assert res.status_code == 200

    # 4. FOLIO (FCE)
    folio_trace = f"FOL-{uuid.uuid4().hex[:8]}"
    folio_data = {"external_reservation_id": str(reservation_id), "trace_id": folio_trace}
    res = client.post("/api/v1/finance/folios", json=folio_data, headers=headers)
    assert res.status_code == 200
    folio_id = res.json()["id"]

    # 5. CHARGE (FCE)
    charge_trace = f"CH-{uuid.uuid4().hex[:8]}"
    charge_data = {"trace_id": charge_trace, "type": "room", "base_amount": 2000.0, "description": "Sovereign Charge"}
    res = client.post(f"/api/v1/finance/folios/{folio_id}/charges", json=charge_data, headers=headers)
    assert res.status_code == 200
    # 2000 + 10%(200) + 17%(2200=374) = 2574.0
    assert res.json()["amount"] == 2574.0

    # 6. TRANSACTION (FCE)
    pay_trace = f"PAY-{uuid.uuid4().hex[:8]}"
    payment_data = {"trace_id": pay_trace, "amount": 2574.0, "method": "credit_card"}
    res = client.post(f"/api/v1/finance/folios/{folio_id}/payments", json=payment_data, headers=headers)
    assert res.status_code == 200

    # 7. FINALIZE (FCE)
    res = client.post(f"/api/v1/finance/folios/{folio_id}/finalize", headers=headers)
    assert res.status_code == 200
    assert res.json()["total_amount"] == 2574.0

    # 8. SHADOW AUDIT VERIFICATION
    # Check if SHADOW entries exist for these traces
    from mnos.modules.shadow import models as shadow_models
    db = TestingSessionLocal()
    audit = db.query(shadow_models.Evidence).filter(shadow_models.Evidence.trace_id == charge_trace).first()
    assert audit is not None
    assert audit.action == "POST_CHARGE"
    assert audit.entity_type == "FOLIO_LINE"

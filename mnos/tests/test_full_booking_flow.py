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
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_mnos_stabilization.db"
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

def test_mnos_stabilization_flow():
    os.environ["TESTING"] = "1"
    headers = get_auth_header()

    # Pre-req: Guest and Room
    guest_res = client.post("/api/v1/guests/", json={"first_name": "Bob", "last_name": "Stable", "email": "bob@mnos.com"}, headers=headers)
    guest_id = guest_res.json()["id"]
    room_res = client.post("/api/v1/reservations/rooms", json={"room_number": "S1", "room_type": "Suite"}, headers=headers)
    room_id = room_res.json()["id"]

    # 1. RESERVATION
    reservation_data = {
        "guest_id": guest_id,
        "total_amount": 0.0,
        "stays": [{"room_id": room_id, "check_in_date": str(date.today()), "check_out_date": str(date.today())}]
    }
    res = client.post("/api/v1/reservations/", json=reservation_data, headers=headers)
    assert res.status_code == 200
    reservation_id = res.json()["id"]

    # 2. TRANSFER
    transfer_data = {
        "reservation_id": reservation_id,
        "type": "boat",
        "pickup_location": "Airport",
        "destination": "Stable Resort"
    }
    res = client.post("/api/v1/transfers/", json=transfer_data, headers=headers)
    assert res.status_code == 200

    # 3. FOLIO
    folio_trace = f"TR-{uuid.uuid4().hex[:8]}"
    folio_data = {"external_reservation_id": str(reservation_id), "trace_id": folio_trace}
    res = client.post("/api/v1/finance/folios", json=folio_data, headers=headers)
    assert res.status_code == 200
    folio_id = res.json()["id"]

    # 4. CHARGE
    charge_trace = f"CH-{uuid.uuid4().hex[:8]}"
    charge_data = {"trace_id": charge_trace, "type": "room", "base_amount": 1000.0, "description": "Stabilization Charge"}
    res = client.post(f"/api/v1/finance/folios/{folio_id}/charges", json=charge_data, headers=headers)
    assert res.status_code == 200
    # 1000 + 10%(100) + 17%(1100=187) = 1287.0
    assert res.json()["amount"] == 1287.0

    # 5. PAYMENT
    payment_trace = f"PY-{uuid.uuid4().hex[:8]}"
    payment_data = {"trace_id": payment_trace, "amount": 1287.0, "method": "cash"}
    res = client.post(f"/api/v1/finance/folios/{folio_id}/payments", json=payment_data, headers=headers)
    assert res.status_code == 200

    # 6. CLOSE (Finalize Invoice)
    res = client.post(f"/api/v1/finance/folios/{folio_id}/finalize", headers=headers)
    assert res.status_code == 200
    assert res.json()["total_amount"] == 1287.0

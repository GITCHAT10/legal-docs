import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime
import uuid
import os

from mnos.interfaces.prestige.main import app
from mnos.core.db.base_class import Base
from mnos.core.api.deps import get_db
from mnos.core.security.security import get_password_hash
from mnos.core.models.user import User
from mnos.core.db import session as db_session

# Ensure all models are loaded
from mnos.interfaces.prestige.guests import models as guest_models
from mnos.modules.inn.reservations import models as res_models
from mnos.modules.aqua.transfers import models as transfer_models
from mnos.modules.fce import models as fce_models
from mnos.modules.shadow import models as shadow_models

# Mock DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./mnos_test.db"
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
    os.environ["TESTING"] = "1"
    db_session.engine = engine
    db_session.SessionLocal = TestingSessionLocal

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Create a superuser
    user = User(
        email="admin@prestige.com",
        hashed_password=get_password_hash("admin"),
        is_superuser=True,
        full_name="Admin"
    )
    db.add(user)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("mnos_test.db"):
        os.remove("mnos_test.db")

def test_full_integrated_flow():
    headers = get_auth_header()

    # 1. Create a Guest
    guest_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "nationality": "British"
    }
    response = client.post("/api/v1/guests/", json=guest_data, headers=headers)
    assert response.status_code == 200
    guest_id = response.json()["id"]

    # 2. Create a Room
    room_data = {
        "room_number": "101",
        "room_type": "Beach Villa",
        "base_price": 500.0
    }
    response = client.post("/api/v1/reservations/rooms", json=room_data, headers=headers)
    assert response.status_code == 200
    room_id = response.json()["id"]

    # 3. Create a Reservation
    reservation_data = {
        "guest_id": guest_id,
        "total_amount": 1000.0,
        "stays": [
            {
                "room_id": room_id,
                "check_in_date": str(date.today()),
                "check_out_date": str(date.today())
            }
        ]
    }
    response = client.post("/api/v1/reservations/", json=reservation_data, headers=headers)
    assert response.status_code == 200
    reservation_id = response.json()["id"]
    external_reservation_id = response.json().get("reservation_id", str(reservation_id))

    # 4. Confirm Reservation (Should trigger auto-transfer)
    response = client.patch(
        f"/api/v1/reservations/{reservation_id}/status",
        json={"status": "confirmed"},
        headers=headers
    )
    assert response.status_code == 200

    # Verify Transfer Request was created
    response = client.get("/api/v1/transfers/", headers=headers)
    transfers = response.json()
    assert len(transfers) > 0

    # 5. Housekeeping marks room as READY
    task_data = {"room_id": room_id, "description": "Initial cleaning"}
    response = client.post("/api/v1/housekeeping/", json=task_data, headers=headers)
    task_id = response.json()["id"]
    response = client.patch(f"/api/v1/housekeeping/{task_id}", json={"status": "completed"}, headers=headers)
    assert response.status_code == 200

    # Verify Room is now READY
    response = client.get("/api/v1/reservations/rooms/", headers=headers)
    rooms = response.json()
    room_101 = next(r for r in rooms if r["id"] == room_id)
    assert room_101["status"] == "ready"

    # 6. Finance - Create Folio and Post Charges
    trace_id_folio = f"trace-folio-{uuid.uuid4().hex}"
    response = client.post(
        f"/api/v1/finance/folios?reservation_id={external_reservation_id}&trace_id={trace_id_folio}",
        headers=headers
    )
    assert response.status_code == 200
    folio_id = response.json()["id"]

    # Post a room charge
    trace_id_charge = f"trace-charge-{uuid.uuid4().hex}"
    charge_data = {
        "folio_id": folio_id,
        "trace_id": trace_id_charge,
        "base_amount": 500.0,
        "description": "Room Charge Night 1",
        "type": "room"
    }
    response = client.post("/api/v1/finance/charges", json=charge_data, headers=headers)
    assert response.status_code == 200
    charge_amount = float(response.json()["amount"])
    # 500 + 10% (50) + 17% of 550 (93.5) = 643.5
    assert charge_amount == 643.5

    # 7. Payment
    trace_id_pay = f"trace-pay-{uuid.uuid4().hex}"
    payment_data = {
        "folio_id": folio_id,
        "trace_id": trace_id_pay,
        "amount": charge_amount,
        "method": "credit_card"
    }
    response = client.post("/api/v1/finance/payments", json=payment_data, headers=headers)
    assert response.status_code == 200

    # Verify Folio balance
    response = client.get(f"/api/v1/finance/folios/{folio_id}", headers=headers)
    assert float(response.json()["paid_amount"]) == 643.5

def get_auth_header():
    response = client.post(
        "/api/v1/login/access-token",
        data={"username": "admin@prestige.com", "password": "admin"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

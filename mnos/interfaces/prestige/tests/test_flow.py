import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime

from mnos.interfaces.prestige.main import app
from mnos.core.db.base_class import Base
from mnos.core.api.deps import get_db
from mnos.core.security.security import get_password_hash
from mnos.core.models.user import User
from mnos.modules.inn.reservations.models import ReservationStatus, RoomStatus
from mnos.modules.aqua.transfers.models import TransferStatus
from mnos.modules.fce.models import PaymentStatus, ChargeType

# Mock DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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
        email="admin@prestige.com",
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
        data={"username": "admin@prestige.com", "password": "admin"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

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
    assert transfers[0]["reservation_id"] == reservation_id

    # 5. Housekeeping marks room as DIRTY then READY
    # First create a task
    task_data = {
        "room_id": room_id,
        "description": "Initial cleaning"
    }
    response = client.post("/api/v1/housekeeping/", json=task_data, headers=headers)
    task_id = response.json()["id"]

    # Complete task
    response = client.patch(f"/api/v1/housekeeping/{task_id}", json={"status": "completed"}, headers=headers)
    assert response.status_code == 200

    # Verify Room is now READY
    response = client.get("/api/v1/reservations/rooms/", headers=headers)
    rooms = response.json()
    room_101 = next(r for r in rooms if r["id"] == room_id)
    assert room_101["status"] == "ready"

    # 6. Finance - Create Folio and Post Charges
    response = client.post(f"/api/v1/finance/folios?reservation_id={reservation_id}", headers=headers)
    assert response.status_code == 200
    folio_id = response.json()["id"]

    # Post a room charge
    charge_data = {
        "folio_id": folio_id,
        "base_amount": 500.0,
        "description": "Room Charge Night 1",
        "charge_type": "room"
    }
    response = client.post(
        f"/api/v1/finance/charges?folio_id={folio_id}&base_amount=500&description=Room%20Charge&charge_type=room",
        headers=headers
    )
    assert response.status_code == 200
    charge_amount = response.json()["amount"]
    # 500 + 10% (50) + 17% of 550 (93.5) = 643.5
    assert charge_amount == 643.5

    # 7. Payment
    payment_data = {
        "folio_id": folio_id,
        "amount": charge_amount,
        "method": "credit_card"
    }
    response = client.post("/api/v1/finance/payments", json=payment_data, headers=headers)
    assert response.status_code == 200

    # Verify Folio is PAID
    response = client.get(f"/api/v1/finance/folios/{folio_id}", headers=headers)
    assert response.json()["status"] == "paid"

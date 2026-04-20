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
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_end_to_end.db"
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

def test_full_booking_flow():
    os.environ["TESTING"] = "1"
    headers = get_auth_header()

    # 1. Create a Guest
    guest_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@mnos.com"
    }
    response = client.post("/api/v1/guests/", json=guest_data, headers=headers)
    assert response.status_code == 200
    guest_id = response.json()["id"]

    # 2. Create a Room (Static route /rooms tested here)
    room_data = {
        "room_number": "101",
        "room_type": "Beach Villa"
    }
    response = client.post("/api/v1/reservations/rooms", json=room_data, headers=headers)
    assert response.status_code == 200
    room_id = response.json()["id"]

    # 3. Create a Reservation (INN)
    reservation_data = {
        "guest_id": guest_id,
        "total_amount": 0.0,
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

    # 4. Open Folio (FCE)
    trace_id = f"TR-{uuid.uuid4().hex[:8]}"
    folio_data = {
        "external_reservation_id": str(reservation_id),
        "trace_id": trace_id
    }
    response = client.post("/api/v1/finance/folios", json=folio_data, headers=headers)
    assert response.status_code == 200
    folio_id = response.json()["id"]

    # 5. Add Charge (FolioLine)
    charge_trace = f"CH-{uuid.uuid4().hex[:8]}"
    charge_data = {
        "trace_id": charge_trace,
        "type": "room",
        "base_amount": 500.0,
        "description": "Room charge",
        "apply_green_tax": True,
        "nights": 1
    }
    response = client.post(f"/api/v1/finance/folios/{folio_id}/charges", json=charge_data, headers=headers)
    assert response.status_code == 200
    # 500 + 10%(50) + 17%(550=93.5) + 6 = 649.5
    assert response.json()["amount"] == 649.5

    # 6. Post Payment
    payment_trace = f"PY-{uuid.uuid4().hex[:8]}"
    payment_data = {
        "trace_id": payment_trace,
        "amount": 649.5,
        "method": "credit_card"
    }
    response = client.post(f"/api/v1/finance/folios/{folio_id}/payments", json=payment_data, headers=headers)
    assert response.status_code == 200

    # 7. Create Transfer (AQUA)
    transfer_data = {
        "reservation_id": reservation_id,
        "type": "boat",
        "pickup_location": "Airport",
        "destination": "Resort"
    }
    response = client.post("/api/v1/transfers/", json=transfer_data, headers=headers)
    assert response.status_code == 200

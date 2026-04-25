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
from mnos.modules.shadow import models as shadow_models

# Mock DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_mnos_comprehensive.db"
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
    user = User(email="admin@mnos.com", hashed_password=get_password_hash("admin"), is_superuser=True, full_name="Admin")
    db.add(user)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def get_auth_header():
    response = client.post("/api/v1/login/access-token", data={"username": "admin@mnos.com", "password": "admin"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

def test_shadow_evidence_chaining():
    headers = get_auth_header()

    # 1. Trigger multiple state changes
    guest_res = client.post("/api/v1/guests/", json={"first_name": "Audit", "last_name": "Test", "email": "audit@mnos.com"}, headers=headers)
    guest_id = guest_res.json()["id"]

    res_data = {"guest_id": guest_id, "stays": [], "adults": 1}
    reservation_id = client.post("/api/v1/reservations/", json=res_data, headers=headers).json()["id"]

    # 2. Check SHADOW evidence
    db = TestingSessionLocal()
    evidences = db.query(shadow_models.Evidence).order_by(shadow_models.Evidence.id.asc()).all()

    assert len(evidences) >= 1
    # Verify hash chaining
    for i in range(1, len(evidences)):
        assert evidences[i].previous_hash == evidences[i-1].current_hash

    # Verify content
    last_evidence = evidences[-1]
    assert last_evidence.entity_type == "RESERVATION"
    assert last_evidence.action == "CREATE_RESERVATION"

def test_over_occupancy_blocking():
    headers = get_auth_header()

    # 1. Create Small Room (Capacity 2)
    room_res = client.post("/api/v1/reservations/rooms", json={"room_number": "SMALL1", "room_type": "Studio", "capacity": 2}, headers=headers)
    room_id = room_res.json()["id"]

    # 2. Attempt Over-occupancy Booking (3 adults)
    res_data = {
        "guest_id": 1,
        "adults": 3,
        "children": 0,
        "stays": [{"room_id": room_id, "check_in_date": str(date.today()), "check_out_date": str(date.today())}]
    }
    res = client.post("/api/v1/reservations/", json=res_data, headers=headers)
    assert res.status_code == 400 or res.status_code == 500 # Capacity validation error

def test_no_show_transfer_auto_cancel():
    headers = get_auth_header()

    # 1. Create Reservation + Transfer
    res_data = {"guest_id": 1, "stays": []}
    reservation_id = client.post("/api/v1/reservations/", json=res_data, headers=headers).json()["id"]

    transfer_data = {"reservation_id": reservation_id, "type": "boat", "pickup_location": "MLE", "destination": "Resort"}
    transfer_res = client.post("/api/v1/transfers/", json=transfer_data, headers=headers)
    transfer_id = transfer_res.json()["id"]

    # 2. Mark No-show
    client.patch(f"/api/v1/reservations/{reservation_id}", json={"status": "no_show"}, headers=headers)

    # 3. Verify Transfer is CANCELLED
    t_status = client.get(f"/api/v1/transfers/{transfer_id}", headers=headers).json()
    assert t_status["status"] == "cancelled"

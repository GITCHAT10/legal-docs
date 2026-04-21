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

# Mock DB for production verification
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_prod_verify.db"
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
    # Create a superuser for auth
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

def test_boot_and_routes():
    headers = get_auth_header()

    # 1. Verify /reservations/rooms is reachable
    res = client.get("/api/v1/inn/reservations/rooms", headers=headers)
    assert res.status_code == 200

    # 2. Verify /transfers/vehicles is reachable
    res = client.get("/api/v1/transfers/vehicles", headers=headers)
    assert res.status_code == 200

def test_folio_flow_end_to_end():
    headers = get_auth_header()

    # 1. Create Guest
    guest_trace = f"G-{uuid.uuid4().hex[:8]}"
    guest_res = client.post("/api/v1/guests/", json={
        "first_name": "Verify",
        "last_name": "User",
        "email": f"verify-{uuid.uuid4().hex[:4]}@mnos.com",
        "trace_id": guest_trace
    }, headers=headers)
    assert guest_res.status_code == 200
    guest_id = guest_res.json()["id"]

    # 2. Create Reservation
    res_trace = f"R-{uuid.uuid4().hex[:8]}"
    reservation_data = {
        "guest_id": guest_id,
        "trace_id": res_trace,
        "stays": []
    }
    res = client.post("/api/v1/inn/reservations/", json=reservation_data, headers=headers)
    assert res.status_code == 200
    reservation_id = res.json()["id"]

    # 3. Create Folio
    folio_trace = f"F-{uuid.uuid4().hex[:8]}"
    res = client.post("/api/v1/finance/folios", json={
        "external_reservation_id": str(reservation_id),
        "trace_id": folio_trace
    }, headers=headers)
    assert res.status_code == 200
    folio_id = res.json()["id"]

    # 4. Post Charge
    charge_trace = f"C-{uuid.uuid4().hex[:8]}"
    res = client.post(f"/api/v1/finance/folios/{folio_id}/charges", json={
        "trace_id": charge_trace,
        "type": "room",
        "base_amount": 100.0,
        "description": "Verification Charge"
    }, headers=headers)
    assert res.status_code == 200
    assert res.json()["amount"] == 128.7 # 100 + 10%(10) + 17%(18.7)

    # 5. Post Payment (Transaction)
    pay_trace = f"P-{uuid.uuid4().hex[:8]}"
    res = client.post(f"/api/v1/finance/folios/{folio_id}/payments", json={
        "trace_id": pay_trace,
        "amount": 128.7,
        "method": "cash"
    }, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "posted"

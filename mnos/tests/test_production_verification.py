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

# Mock DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_verification.db"
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

def test_routes_ordering():
    headers = get_auth_header()

    # 1. Verify /reservations/rooms is reachable
    res = client.get("/api/v1/inn/reservations/rooms", headers=headers)
    assert res.status_code == 200

    # 2. Verify /transfers/vehicles is reachable
    res = client.get("/api/v1/transfers/vehicles", headers=headers)
    assert res.status_code == 200

def test_full_financial_flow():
    headers = get_auth_header()

    # 1. Create Folio
    folio_trace = f"F-{uuid.uuid4().hex[:4]}"
    res = client.post("/api/v1/finance/folios", json={
        "external_reservation_id": "RES-123",
        "trace_id": folio_trace,
        "tenant_id": "default"
    }, headers=headers)
    assert res.status_code == 200
    folio_id = res.json()["id"]

    # 2. Post Charge
    charge_trace = f"C-{uuid.uuid4().hex[:4]}"
    res = client.post(f"/api/v1/finance/folios/{folio_id}/charges", json={
        "trace_id": charge_trace,
        "type": "room",
        "base_amount": 100.0,
        "description": "Verification Charge",
        "tenant_id": "default"
    }, headers=headers)
    assert res.status_code == 200
    assert res.json()["amount"] == 127.6 # 100 + 10%(10) + 16%(17.6) for current date

    # 3. Post Payment
    pay_trace = f"P-{uuid.uuid4().hex[:4]}"
    res = client.post(f"/api/v1/finance/folios/{folio_id}/payments", json={
        "trace_id": pay_trace,
        "amount": 127.6,
        "method": "cash",
        "tenant_id": "default"
    }, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "posted"

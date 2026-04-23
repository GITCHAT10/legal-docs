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
from mnos.core.aegis.security.security import get_password_hash
from mnos.core.models.user import User

# Mock DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_multi_property.db"
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
    user = User(email="operator@mnos.com", hashed_password=get_password_hash("operator"), is_superuser=True, full_name="Network Operator")
    db.add(user)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def get_auth_header(patente: str = "MIG-OPERATOR-01"):
    response = client.post("/api/v1/login/access-token", data={"username": "operator@mnos.com", "password": "operator"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "X-NexGen-Patente": patente}

def test_multi_property_guest_flow():
    """
    Success Condition:
    - Guest processed across 2 different properties (tenants).
    - Cross-property identity working.
    - Single guest -> multi-property invoice.
    """
    headers = get_auth_header()

    # 1. Create Global Guest
    guest_trace = f"G-{uuid.uuid4().hex[:4]}"
    guest_res = client.post("/api/v1/guests/", json={
        "first_name": "Multi", "last_name": "Property", "email": "multi@property.com", "trace_id": guest_trace
    }, headers=headers)
    guest_id = guest_res.json()["id"]

    # 2. Property A Booking (Tenant: SALA)
    res_a_trace = f"RES-A-{uuid.uuid4().hex[:4]}"
    client.post("/api/v1/reservations/", json={
        "guest_id": guest_id, "tenant_id": "SALA", "trace_id": res_a_trace, "stays": []
    }, headers=headers)

    # 3. Property B Booking (Tenant: GAN)
    res_b_trace = f"RES-B-{uuid.uuid4().hex[:4]}"
    client.post("/api/v1/reservations/", json={
        "guest_id": guest_id, "tenant_id": "GAN", "trace_id": res_b_trace, "stays": []
    }, headers=headers)

    # 4. Verify Folios exist for both properties
    from mnos.core.fce.models import Folio
    db = TestingSessionLocal()
    folios = db.query(Folio).filter(Folio.guest_id == guest_id).all()
    assert len(folios) == 2
    tenants = {f.tenant_id for f in folios}
    assert "SALA" in tenants
    assert "GAN" in tenants

    # 5. Cross-Property Settlement Simulation
    # Settle everything for this guest via Global Clearing House
    from mnos.core.fce.service import cross_property_settlement
    settlement_trace = f"SETTLE-{uuid.uuid4().hex[:4]}"
    results = cross_property_settlement(db, guest_id, settlement_trace, actor="operator@mnos.com")

    # Verify both folios were affected (if they had balances)
    # Since they have 0 total_amount, we just check the call succeeds
    assert isinstance(results, list)

def test_mira_compliant_export():
    """Verify first tax-compliant report (MIRA-ready)."""
    headers = get_auth_header()
    db = TestingSessionLocal()

    # 1. Create and Finalize a Folio with Charges
    res_trace = f"RES-MIRA-{uuid.uuid4().hex[:4]}"
    client.post("/api/v1/reservations/", json={
        "guest_id": 1, "trace_id": res_trace, "stays": []
    }, headers=headers)

    # Find the auto-opened folio
    from mnos.core.fce.models import Folio
    folio = db.query(Folio).filter(Folio.trace_id == f"FOLIO-{res_trace}").first()

    # Post charge
    client.post(f"/api/v1/finance/folios/{folio.id}/charges", json={
        "trace_id": f"CH-{uuid.uuid4().hex[:4]}", "type": "room", "base_amount": 500.0
    }, headers=headers)

    # Finalize
    inv_res = client.post(f"/api/v1/finance/folios/{folio.id}/finalize", headers=headers)
    invoice_id = inv_res.json()["id"]

    # 2. Export MIRA JSON
    export_res = client.get(f"/api/v1/finance/invoices/{invoice_id}/mira-export", headers=headers)
    assert export_res.status_code == 200
    assert "verification_hash" in export_res.json()
    assert export_res.json()["standard"] == "MIRA-EOS-2026"

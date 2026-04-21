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
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_revenue_engine.db"
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
    user = User(email="revenue@mnos.com", hashed_password=get_password_hash("rev"), is_superuser=True, full_name="Revenue Admin")
    db.add(user)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def test_revenue_distribution_authority():
    """Verify the 'Sovereign Profit Loop': Contract -> Sale -> Distribution."""
    db = TestingSessionLocal()
    from mnos.modules.revenue import service as rev_service
    from mnos.modules.fce import service as fce_service

    # 1. CONTRACT DEFINITION (GOVERN)
    contract = rev_service.create_partner_contract(db, {
        "partner_name": "Luxury Diving Ltd",
        "partner_type": "VENDOR",
        "share_percentage": 30.0,
        "payout_timing": "IMMEDIATE"
    }, trace_id=f"CON-{uuid.uuid4().hex[:4]}")

    # 2. SALE (FCE)
    folio = fce_service.open_folio(db, "RES-DIVING-01", f"TR-{uuid.uuid4().hex[:4]}")
    line = fce_service.post_charge(db, folio.id, {
        "type": "other", "base_amount": 100.0, "description": "Dolphin Excursion"
    }, trace_id=f"CH-{uuid.uuid4().hex[:4]}")

    # 3. REVENUE DISTRIBUTION (REVENUE)
    split = rev_service.calculate_distribution(db, line.id, contract.id, f"SPLIT-{uuid.uuid4().hex[:4]}")

    # Verify split logic (30% of 100)
    assert split.partner_amount == 30.0
    assert split.resort_amount == 70.0

    # 4. SHADOW TRACE
    from mnos.modules.shadow.models import Evidence
    evidence = db.query(Evidence).filter(Evidence.entity_type == "REVENUE_SPLIT", Evidence.entity_id == str(split.id)).first()
    assert evidence is not None
    assert evidence.after_state["partner_amount"] == 30.0

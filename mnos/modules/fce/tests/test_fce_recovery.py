import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import uuid
from mnos.core.db.base_class import Base
from mnos.modules.fce import models, service, tax_logic

SQLALCHEMY_DATABASE_URL = "sqlite:///./fce_recovery_test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("fce_recovery_test.db"):
        os.remove("fce_recovery_test.db")

def test_fce_core_financial_flow():
    db = TestingSessionLocal()
    res_id = "RES-999"
    trace_id_folio = f"trace-folio-{uuid.uuid4().hex}"
    folio = service.open_folio(db, res_id, trace_id_folio)
    assert folio.id is not None
    assert folio.external_reservation_id == res_id
    trace_id_charge = f"trace-charge-{uuid.uuid4().hex}"
    charge_data = {"type": models.ChargeType.ROOM, "base_amount": 1000.0, "description": "Luxury Villa Night"}
    line = service.post_charge(db, folio.id, charge_data, trace_id_charge)
    assert line.id is not None
    db.refresh(folio)
    assert float(folio.total_amount) == 1287.0
    trace_id_pay = f"trace-pay-{uuid.uuid4().hex}"
    payment = service.process_payment(db, folio.id, {"amount": 1287.0, "method": "CREDIT_CARD"}, trace_id_pay)
    db.refresh(folio)
    assert float(folio.paid_amount) == 1287.0
    db.close()

def test_fail_closed_idempotency():
    db = TestingSessionLocal()
    res_id = "RES-DUP"
    trace_id = "trace-unique-123"
    f1 = service.open_folio(db, res_id, trace_id)
    f2 = service.open_folio(db, res_id, trace_id)
    assert f1.id == f2.id
    db.close()

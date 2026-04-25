import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decimal import Decimal
import os
import uuid
from mnos.core.db.base_class import Base
from mnos.modules.fce import models, service, tax_logic
from mnos.modules.shadow import models as shadow_models

SQLALCHEMY_DATABASE_URL = "sqlite:///./fce_fail_closed_test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("fce_fail_closed_test.db"):
        os.remove("fce_fail_closed_test.db")

def test_trace_id_uniqueness():
    db = TestingSessionLocal()
    trace_id = "unique-trace-123"
    service.open_folio(db, "RES-1", trace_id)
    f2 = service.open_folio(db, "RES-2", trace_id)
    assert f2.external_reservation_id == "RES-1"
    service.post_charge(db, f2.id, {"type": "room", "base_amount": 100}, "trace-charge-1")
    c2 = service.post_charge(db, f2.id, {"type": "room", "base_amount": 200}, "trace-charge-1")
    assert c2.base_amount == Decimal("100.0000")
    db.close()

def test_atomic_rollback_on_failure():
    db = TestingSessionLocal()
    trace_id = "trace-rollback"
    folio = service.open_folio(db, "RES-ROLL", "trace-folio-roll")
    initial_total = folio.total_amount
    with pytest.raises(Exception):
        service.post_charge(db, folio.id, {"type": None}, trace_id)
    db.refresh(folio)
    assert folio.total_amount == initial_total
    db.close()

def test_decimal_precision_mira():
    taxes = tax_logic.calculate_maldives_taxes(Decimal("1000.33"))
    assert taxes["service_charge"] == Decimal("100.03")
    assert taxes["tgst"] == Decimal("187.06")
    assert taxes["total_amount"] == Decimal("1287.42")

def test_outbox_pattern():
    db = TestingSessionLocal()
    trace_id = f"trace-outbox-{uuid.uuid4().hex}"
    service.open_folio(db, "RES-OUT", trace_id)
    outbox = db.query(models.OutboxEvent).filter(models.OutboxEvent.trace_id == f"evt-{trace_id}").first()
    assert outbox is not None
    assert outbox.processed is False
    service.flush_outbox(db)
    db.refresh(outbox)
    assert outbox.processed is True
    db.close()

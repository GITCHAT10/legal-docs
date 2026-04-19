import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from mnos.core.db.base_class import Base
from mnos.interfaces.prestige.service import PrestigeBookingService
from mnos.modules.fce import models as fce_models
from mnos.modules.shadow import models as shadow_models

# Mock DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./mnos_test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_mnos_integrated_flow():
    db = TestingSessionLocal()
    os.environ["TESTING"] = "1"

    # 1. Initialize Prestige Interface
    prestige = PrestigeBookingService(db)

    # 2. Capture Booking Intent
    booking_data = {
        "guest_name": "Jane Doe",
        "dates": "2024-05-01 to 2024-05-05",
        "villa_type": "Overwater"
    }
    result = prestige.create_booking_intent(booking_data)

    # 3. Verify Result
    assert result["status"] == "committed"
    assert "reservation_id" in result
    assert "trace_id" in result

    # 4. Verify FCE (Authority)
    folio = db.query(fce_models.Folio).filter(fce_models.Folio.id == result["folio_id"]).first()
    assert folio is not None
    assert folio.external_reservation_id == result["reservation_id"]

    # 5. Verify SHADOW (Evidence)
    evidence = db.query(shadow_models.Evidence).filter(shadow_models.Evidence.id == result["shadow_id"]).first()
    assert evidence is not None
    assert evidence.trace_id == result["trace_id"]
    assert "mnos_response" in evidence.payload

    db.close()

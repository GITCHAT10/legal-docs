import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from mnos.core.db.base_class import Base
from mnos.interfaces.prestige.service import PrestigeBookingService
from mnos.modules.fce import models as fce_models
from mnos.modules.shadow import models as shadow_models

SQLALCHEMY_DATABASE_URL = "sqlite:///./mnos_test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("mnos_test.db"):
        os.remove("mnos_test.db")

def test_mnos_integrated_flow():
    db = TestingSessionLocal()
    os.environ["TESTING"] = "1"
    prestige = PrestigeBookingService(db)
    booking_data = {"guest_name": "Jane Doe", "dates": "2024-05-01 to 2024-05-05", "villa_type": "Overwater"}
    result = prestige.create_booking_intent(booking_data)
    assert result["status"] == "committed"
    db.close()

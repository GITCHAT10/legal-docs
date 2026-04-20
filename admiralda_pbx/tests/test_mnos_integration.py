import pytest
from mnos.adapters.admiralda_connect import admiralda_connect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from mnos.core.db.base_class import Base
from mnos.core.db import session as db_session
from mnos.modules.shadow import models as shadow_models
from mnos.modules.fce import models as fce_models
import os

# Use the same DB as MNOS client would expect in testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./mnos_test_integration.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    os.environ["TESTING"] = "1"
    # Ensure the engine in db_session is also using the same URL
    db_session.engine = engine
    db_session.SessionLocal = TestingSessionLocal

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("mnos_test_integration.db"):
        os.remove("mnos_test_integration.db")

def test_mnos_voice_verification():
    payload = {
        "voiceprint_id": "VP-9921",
        "voiceprint_match": 0.97,
        "intent_phrase": "I confirm the revised transfer and credit"
    }
    result = admiralda_connect.verify_voice_identity(payload)
    assert result["status"] == "VERIFIED"
    assert result["persona"] == "VP-9921"

def test_mnos_preauthorize_buffer():
    payload = {
        "tenant_id": "RESORT-001",
        "ltv": 20000,
        "risk_of_churn": 0.72,
        "requested_buffer": 350
    }
    result = admiralda_connect.preauthorize_buffer(payload)
    assert result["status"] == "AUTHORIZED"
    assert result["amount"] == 350

def test_mnos_seal_evidence():
    payload = {
        "call_id": "CALL-123",
        "audio_hash": "sha256:abc",
        "transcript_hash": "sha256:def",
        "envelope_hash": "sha256:ghi",
        "intent_score": 0.93
    }
    result = admiralda_connect.seal_evidence(payload)
    assert result["status"] == "SEALED"
    assert "shadow_id" in result
    assert "shadow_signature" in result

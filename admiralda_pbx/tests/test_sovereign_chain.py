import pytest
from fastapi.testclient import TestClient
from admiralda_pbx.apps.api.main import app
from mnos.adapters.admiralda_connect import admiralda_connect
from mnos.core.db.base_class import Base
from mnos.core.db import session as db_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import uuid

# Setup real DB for integration chain test
SQLALCHEMY_DATABASE_URL = "sqlite:///./mnos_test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    os.environ["TESTING"] = "1"
    db_session.engine = engine
    db_session.SessionLocal = TestingSessionLocal

    # Load all models for Base to see them
    from mnos.modules.fce import models as fce_models
    from mnos.modules.shadow import models as shadow_models

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("mnos_test.db"):
        os.remove("mnos_test.db")

client = TestClient(app)

def test_sovereign_execution_chain():
    """
    Integration Test: voice -> PBX -> FCE -> SHADOW -> commit
    """
    # 1. Voice Ingest (Transcript)
    payload = {
        "tenant_id": "RESORT-001",
        "caller_id": "+9607771234",
        "call_id": f"CALL-{uuid.uuid4().hex[:6]}",
        "transcript": "I confirm the booking and authorize the 1287 dollar payment now.",
        "voiceprint_match": 0.99
    }

    # PBX API Call
    response = client.post("/api/v1/ingest", json=payload)
    assert response.status_code == 200
    pbx_data = response.json()

    assert pbx_data["decision"] == "INITIATE_DUAL_CONFIRMATION"
    assert pbx_data["execution_status"] == "PENDING_CONFIRMATION"

    # 2. PBX -> MNOS (Adapter Call - simulating what happens after dual confirmation)
    trace_id = pbx_data["trace_id"]

    # Real FCE Execution: Open Folio
    folio_resp = admiralda_connect.preauthorize_buffer({
        "tenant_id": "RESORT-001",
        "ltv": 20000,
        "risk_of_churn": 0.7,
        "requested_buffer": 1287.0
    })
    assert folio_resp["status"] == "AUTHORIZED"

    # Real SHADOW Execution: Seal Evidence
    seal_resp = admiralda_connect.seal_evidence({
        "call_id": payload["call_id"],
        "audio_hash": pbx_data["evidence_envelope"]["audio_hash"],
        "transcript_hash": pbx_data["evidence_envelope"]["transcript_hash"],
        "envelope_hash": pbx_data["evidence_envelope"]["envelope_hash"],
        "intent_score": pbx_data["evidence_envelope"]["intent_score"],
        "execution_status": "COMMITTED",
        "consent_confirmed": True,
        "trace_id": trace_id
    })

    assert seal_resp["status"] == "SEALED"
    assert "shadow_signature" in seal_resp

    # 3. Verify Commit in Ledger
    from mnos.modules.shadow.service import fetch_evidence
    db = TestingSessionLocal()
    evidence = fetch_evidence(db, trace_id)
    assert evidence is not None
    assert evidence.payload["execution_status"] == "COMMITTED"
    db.close()

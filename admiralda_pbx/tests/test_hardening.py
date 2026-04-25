import pytest
from fastapi.testclient import TestClient
from admiralda_pbx.apps.api.main import app
from admiralda_pbx.integrations.mnos.client import mnos_connect

client = TestClient(app)

def test_rejection_low_intent():
    payload = {
        "tenant_id": "RESORT-001",
        "caller_id": "+9607771234",
        "call_id": "CALL-LOW-INTENT",
        "transcript": "Maybe I want to book something, I am not sure."
    }
    response = client.post("/api/v1/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "REJECT_LOW_INTENT"
    assert data["execution_status"] == "BLOCKED"
    assert "intent score too low" in data["whisper_assist"].lower()

def test_rejection_low_voiceprint():
    payload = {
        "tenant_id": "RESORT-001",
        "caller_id": "+9607771234",
        "call_id": "CALL-LOW-VOICE",
        "transcript": "Yes, please go ahead and confirm my booking.",
        "voiceprint_match": 0.80 # Below 0.95 threshold
    }
    response = client.post("/api/v1/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "REJECT_UNVERIFIED_VOICE"
    assert data["execution_status"] == "BLOCKED"
    assert "voiceprint match failed" in data["whisper_assist"].lower()

def test_fail_closed_mnos_offline():
    # Set MNOS to offline
    mnos_connect.is_offline = True
    try:
        payload = {
            "tenant_id": "RESORT-001",
            "caller_id": "+9607771234",
            "call_id": "CALL-MNOS-OFFLINE",
            "transcript": "Yes, please go ahead and confirm my booking.",
            "voiceprint_match": 0.98
        }
        response = client.post("/api/v1/ingest", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "FAIL_CLOSED"
        assert data["execution_status"] == "FAILED_CLOSED"
        assert "unreachable" in data["whisper_assist"].lower()
    finally:
        mnos_connect.is_offline = False

def test_dual_confirmation_required():
    payload = {
        "tenant_id": "RESORT-001",
        "caller_id": "+9607771234",
        "call_id": "CALL-DUAL-AUTH",
        "transcript": "Yes, please go ahead and confirm my booking.",
        "voiceprint_match": 0.98
    }
    response = client.post("/api/v1/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "INITIATE_DUAL_CONFIRMATION"
    assert data["execution_status"] == "PENDING_CONFIRMATION"
    assert "whatsapp" in data["whisper_assist"].lower()
    assert data["evidence_envelope"]["consent_confirmed"] is False # Waiting for SMS/WhatsApp

def test_risk_matrix_generation():
    payload = {
        "tenant_id": "RESORT-001",
        "caller_id": "+9607771234",
        "call_id": "CALL-RISK",
        "transcript": "Yes, please go ahead and confirm my booking.",
        "voiceprint_match": 0.98
    }
    response = client.post("/api/v1/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_matrix" in data
    assert data["risk_matrix"]["intent_risk"] == "LOW"
    assert data["risk_matrix"]["identity_risk"] == "LOW"
    assert data["risk_matrix"]["overall_score"] > 0.9

import pytest
import json
from fastapi.testclient import TestClient
from admiralda_pbx.apps.api.main import app
from admiralda_pbx.integrations.mnos.client import mnos_connect

client = TestClient(app)

def test_proof_blocked_low_confidence():
    """Prove low-confidence call is BLOCKED"""
    payload = {
        "tenant_id": "RESORT-001",
        "caller_id": "+9607771234",
        "call_id": "PROOF-BLOCKED",
        "transcript": "Maybe... confirm?" # This will likely yield low confidence/intent in a real model
    }
    # In our current mock sentinel, 'confirm' gives 0.95 intent but we need to trigger rejection
    # Let's use a transcript without trigger phrases
    payload["transcript"] = "I am just calling to chat."
    response = client.post("/api/v1/ingest", json=payload)
    data = response.json()
    assert data["execution_status"] == "BLOCKED"
    assert data["decision"] == "REJECT_LOW_INTENT"

def test_proof_pending_high_confidence():
    """Prove high-confidence financial call stays PENDING_CONFIRMATION"""
    payload = {
        "tenant_id": "RESORT-001",
        "caller_id": "+9607771234",
        "call_id": "PROOF-PENDING",
        "transcript": "Yes, please go ahead and confirm my booking.",
        "voiceprint_match": 0.98
    }
    response = client.post("/api/v1/ingest", json=payload)
    data = response.json()
    assert data["execution_status"] == "PENDING_CONFIRMATION"
    assert data["evidence_envelope"]["consent_confirmed"] is False
    assert "whatsapp" in data["whisper_assist"].lower()

def test_proof_failed_closed_mnos_failure():
    """Prove MNOS failure results in FAILED_CLOSED"""
    mnos_connect.is_offline = True
    try:
        payload = {
            "tenant_id": "RESORT-001",
            "caller_id": "+9607771234",
            "call_id": "PROOF-FAIL-CLOSED",
            "transcript": "confirm now!",
            "voiceprint_match": 0.98
        }
        response = client.post("/api/v1/ingest", json=payload)
        data = response.json()
        assert data["execution_status"] == "FAILED_CLOSED"
        assert data["decision"] == "FAIL_CLOSED"
    finally:
        mnos_connect.is_offline = False

def test_capture_artifacts():
    """Capture real sample evidence envelope and risk matrix"""
    payload = {
        "tenant_id": "RESORT-001",
        "caller_id": "+9607771234",
        "call_id": "PROOF-ARTIFACTS",
        "transcript": "I confirm the booking and authorize payment.",
        "voiceprint_match": 0.99
    }
    response = client.post("/api/v1/ingest", json=payload)
    data = response.json()

    with open("evidence_sample.json", "w") as f:
        json.dump(data["evidence_envelope"], f, indent=2)

    with open("risk_matrix_sample.json", "w") as f:
        json.dump(data["risk_matrix"], f, indent=2)

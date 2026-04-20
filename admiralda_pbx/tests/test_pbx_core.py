import pytest
from fastapi.testclient import TestClient
from admiralda_pbx.apps.api.main import app

client = TestClient(app)

def test_pbx_ingest_confirm():
    payload = {
        "tenant_id": "RESORT-001",
        "caller_id": "+9607771234",
        "call_id": "CALL-123",
        "transcript": "Yes, please go ahead and confirm my booking.",
        "voiceprint_match": 0.98
    }
    response = client.post("/api/v1/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PROCESSED"
    assert data["decision"] == "INITIATE_DUAL_CONFIRMATION"
    assert data["evidence_envelope"] is not None
    assert "envelope_hash" in data["evidence_envelope"]
    assert "Triggering WhatsApp/SMS confirmation flow." in data["whisper_assist"]

def test_pbx_ingest_stress():
    payload = {
        "tenant_id": "RESORT-001",
        "caller_id": "+9607771234",
        "call_id": "CALL-456",
        "transcript": "I have a big problem with my flight, it is urgent!"
    }
    response = client.post("/api/v1/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PROCESSED"
    # Stress causes REJECT_LOW_INTENT in this mock because intent score is 0
    assert data["decision"] == "REJECT_LOW_INTENT"
    assert "empathetic de-escalation" in data["whisper_assist"]

def test_pbx_status():
    response = client.get("/api/v1/status/CALL-123?tenant_id=RESORT-001")
    assert response.status_code == 200
    assert response.json()["status"] == "ACTIVE"

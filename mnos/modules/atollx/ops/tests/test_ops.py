import pytest
from fastapi.testclient import TestClient
from main import app, shadow_core, orca_core

client = TestClient(app)

@pytest.fixture
def auth_headers():
    return {
        "X-AEGIS-IDENTITY": "OPS-ADMIN-001",
        "X-AEGIS-DEVICE": "OPS-DEV-001",
        "X-TRACE-ID": "TRACE-OPS-001"
    }

def test_ops_trigger_fails_without_identity():
    response = client.post("/api/atollx/ops/project", json={"project_id": "OP1", "name": "Ops 1"})
    assert response.status_code == 401

def test_jetty_receipt_requires_manifest(auth_headers):
    project_id = "P1"
    payload = {
        "receipt_id": "R1", "project_id": project_id, "barge_manifest_id": "M1",
        "received_quantity": 500, "unit": "kg", "signed_by": "Officer A"
    }
    response = client.post("/api/atollx/ops/logistics/jetty-receipt", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "No linked barge manifest found" in response.json()["detail"]

def test_epa_turbidity_hold(auth_headers):
    payload = {
        "exceedance_id": "E1", "project_id": "P1", "parameter": "TURBIDITY",
        "value": 50.0, "threshold": 10.0, "unit": "NTU"
    }
    response = client.post("/api/atollx/ops/epa/exceedance", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "ENVIRONMENTAL_HOLD"

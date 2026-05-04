import pytest
from fastapi.testclient import TestClient
from main import app, shadow_core, orca_core
from mnos.modules.demo.fenfuraaveli_pilot import FenfuraaveliPilot

client = TestClient(app)

@pytest.fixture
def auth_headers():
    return {
        "X-AEGIS-IDENTITY": "PILOT-ADMIN-001",
        "X-AEGIS-DEVICE": "DEV-001",
        "X-TRACE-ID": "TRACE-FEN-001"
    }

@pytest.fixture
def pilot():
    # Clear chain for each test to avoid interference
    shadow_core.chain = []
    return FenfuraaveliPilot(shadow_core, orca_core, None)

def test_fenfuraaveli_handoff_gate(auth_headers, pilot):
    project_id = "RC_BX_AX_PILOT_001_FENFURAAVELI"

    # Seed and Approve
    pilot.seed_project()
    pilot.simulate_visual_approval("PILOT-ADMIN-001")

    # Try handoff
    response = client.post("/api/redcoral/handoff-to-buildx", json={
        "handoff_id": "H1", "project_id": project_id, "design_baseline_id": "DB1"
    }, headers=auth_headers)
    assert response.status_code == 200

def test_fenfuraaveli_settlement_gate(auth_headers, pilot):
    project_id = "RC_BX_AX_PILOT_001_FENFURAAVELI"

    # Add site evidence
    client.post("/api/buildx/site-evidence", json={
        "evidence_id": "E1", "milestone_id": "M1", "project_id": project_id, "media_urls": [], "description": "Design baseline proof"
    }, headers=auth_headers)

    response = client.post(f"/api/buildx/request-fce-settlement?milestone_id=M1&project_id={project_id}&amount_mvr=1000", headers=auth_headers)
    assert response.status_code == 200

def test_fenfuraaveli_handover_gate(auth_headers, pilot):
    project_id = "RC_BX_AX_PILOT_001_FENFURAAVELI"

    # Add QA/QC
    client.post("/api/buildx/qaqc", json={
        "check_id": "Q1", "project_id": project_id, "category": "General", "passed": True, "findings": "All plots verified"
    }, headers=auth_headers)

    payload = {
        "package_id": "HP1", "project_id": project_id,
        "as_built_drawings_url": "u", "manuals_url": "u", "completion_certificate_url": "u"
    }
    response = client.post("/api/buildx/handover", json=payload, headers=auth_headers)
    assert response.status_code == 200

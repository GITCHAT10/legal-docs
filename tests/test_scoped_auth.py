import pytest
from fastapi.testclient import TestClient
from main import app, shadow_core, orca_core
from mnos.shared.execution_guard import _sovereign_context

client = TestClient(app)

@pytest.fixture
def auth_headers():
    return {
        "X-AEGIS-IDENTITY": "ACTOR-TEST",
        "X-AEGIS-DEVICE": "DEV-TEST",
        "X-TRACE-ID": "TRACE-TEST"
    }

def test_rc_auth_failure():
    # REDCORAL API returns controlled auth failure when actor context is missing.
    response = client.post("/api/redcoral/brief", json={
        "project_id": "P1", "client_id": "C1", "title": "T1", "requirements": [], "budget_range": "10k"
    })
    assert response.status_code == 401
    assert "AEGIS_AUTH_REQUIRED" in response.json()["detail"]

def test_scoped_handoff_prevention(auth_headers):
    # Project B cannot hand off to BUILDX using Project A approval.
    # 1. Approve Project A
    client.post("/api/redcoral/approve-design", json={
        "approval_id": "APP-A", "project_id": "PROJ-A", "approver_id": "ADM", "status": "APPROVED", "approval_hash": "hash"
    }, headers=auth_headers)

    # 2. Attempt handoff for Project B
    response = client.post("/api/redcoral/handoff-to-buildx", json={
        "handoff_id": "H1", "project_id": "PROJ-B", "design_baseline_id": "DB1"
    }, headers=auth_headers)

    assert response.status_code == 400
    assert "Design must be approved" in response.json()["detail"]

def test_scoped_handover_prevention(auth_headers):
    # Project B cannot handover using Project A QA/QC.
    # 1. Log QA/QC for Project A
    client.post("/api/buildx/qaqc", json={
        "check_id": "Q-A", "project_id": "PROJ-A", "category": "General", "passed": True, "findings": "OK"
    }, headers=auth_headers)

    # 2. Attempt handover for Project B
    response = client.post("/api/buildx/handover", json={
        "package_id": "HP1", "project_id": "PROJ-B", "as_built_drawings_url": "u", "manuals_url": "u", "completion_certificate_url": "u"
    }, headers=auth_headers)

    assert response.status_code == 400
    assert "BX QA/QC must be complete" in response.json()["detail"]

def test_scoped_orca_blocker(auth_headers):
    # Settlement for Project B is not blocked by failed ORCA validation from Project A.
    # 1. Failed validation for Project A
    orca_core.validate("CHECK-A", "ACTOR-TEST", {"project_id": "PROJ-A", "passed": False})

    # 2. Add site evidence for Project B
    client.post("/api/buildx/site-evidence", json={
        "evidence_id": "E1", "milestone_id": "M1", "project_id": "PROJ-B", "media_urls": [], "description": "test"
    }, headers=auth_headers)

    # 3. Request settlement for Project B (Should pass)
    response = client.post("/api/buildx/request-fce-settlement?milestone_id=M1&project_id=PROJ-B&amount_mvr=1000", headers=auth_headers)
    assert response.status_code == 200

def test_orca_blocks_same_project(auth_headers):
    # Settlement for Project A is blocked by failed ORCA validation from Project A.
    # 1. Failed validation for Project A
    orca_core.validate("CHECK-A", "ACTOR-TEST", {"project_id": "PROJ-A", "passed": False})

    # 2. Add site evidence for Project A
    client.post("/api/buildx/site-evidence", json={
        "evidence_id": "E2", "milestone_id": "M1", "project_id": "PROJ-A", "media_urls": [], "description": "test"
    }, headers=auth_headers)

    # 3. Request settlement for Project A (Should fail)
    response = client.post("/api/buildx/request-fce-settlement?milestone_id=M1&project_id=PROJ-A&amount_mvr=1000", headers=auth_headers)
    assert response.status_code == 400
    assert "ORCA validation failure blocked FCE settlement" in response.json()["detail"]

def test_shadow_integrity_regression(auth_headers):
    # All accepted actions still write SHADOW events with trace_id, parent_hash, payload_hash, timestamp_utc.
    client.post("/api/redcoral/brief", json={
        "project_id": "P1", "client_id": "C1", "title": "T1", "requirements": [], "budget_range": "10k"
    }, headers=auth_headers)

    event = shadow_core.chain[-1]
    assert "parent_hash" in event
    assert "payload" in event
    assert "timestamp_utc" in event
    assert "hash" in event

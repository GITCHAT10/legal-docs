import pytest
from fastapi.testclient import TestClient
from mnos.modules.education.api.employer import app
from mnos.modules.education.core.digital_twin import DigitalTwinEngine, SimulationResult
from mnos.modules.education.models.schemas import JobDemand, SkillVerification
from datetime import datetime, UTC

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "operational"

def test_post_job_demand():
    demand_data = {
        "id": "JOB-001",
        "employer_id": "EMP-001",
        "title": "AI Resident",
        "required_skills": ["Python", "Machine Learning"],
        "location": "University Island"
    }
    response = client.post("/demand", json=demand_data)
    assert response.status_code == 200
    assert response.json()["id"] == "JOB-001"

def test_digital_twin_engine():
    engine = DigitalTwinEngine()
    result = SimulationResult(
        student_id="STU-001",
        simulation_id="SIM-001",
        score=0.9,
        competencies_demonstrated=["Python", "Data Analysis"]
    )

    twin = engine.ingest_simulation(result)
    assert twin.student_id == "STU-001"
    assert twin.performance_capital > 0
    assert twin.mastery_levels["Python"] == 0.27  # 0.7*0 + 0.3*0.9

def test_predict_pacing():
    engine = DigitalTwinEngine()
    result = SimulationResult(
        student_id="STU-001",
        simulation_id="SIM-001",
        score=0.8,
        competencies_demonstrated=["Python"]
    )
    engine.ingest_simulation(result)

    prediction = engine.predict_pacing("STU-001", "Python")
    assert "predicted_completion" in prediction
    assert prediction["current_level"] == 0.24 # 0.7*0 + 0.3*0.8

def test_skill_verification_endpoint():
    verification_data = {
        "student_id": "STU-001",
        "skill_id": "SKL-001",
        "verified": True,
        "score": 0.95,
        "verifier_id": "VER-001",
        "correlation_id": "CORR-123"
    }
    response = client.post("/verify-skill", json=verification_data)
    assert response.status_code == 200
    assert response.json()["verified"] is True

def test_match_students_endpoint():
    response = client.get("/match/JOB-001")
    assert response.status_code == 200
    assert response.json()[0]["correlation_id"] == "MATCH-CORR-001"

def test_certify_student_endpoint():
    cert_data = {
        "student_id": "STU-001",
        "skill_id": "SKL-001",
        "evidence_hash": "SHA256:FAKEHASH",
        "actor_id": "ADM-001",
        "correlation_id": "CERT-CORR-123"
    }
    response = client.post("/certify", json=cert_data)
    assert response.status_code == 200
    assert response.json()["correlation_id"] == "CERT-CORR-123"

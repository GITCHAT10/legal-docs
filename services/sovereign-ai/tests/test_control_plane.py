from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_high_risk_task_requires_independent_approval() -> None:
    entity = uuid4()
    agent = client.post(
        "/v1/agents",
        headers={"X-Actor-Id": "admin@mig"},
        json={
            "legal_entity_id": str(entity),
            "code": "CFO_TREASURY",
            "name": "CFO Treasury Agent",
            "department": "Finance",
            "allowed_tools": ["treasury.propose_payment"],
            "max_risk": "HIGH",
        },
    ).json()

    payload = {
        "legal_entity_id": str(entity),
        "agent_id": agent["id"],
        "action": "PROPOSE_PAYMENT",
        "payload": {"tool": "treasury.propose_payment", "amount": 1000},
        "risk": "HIGH",
        "idempotency_key": "payment-test-0001",
    }
    first = client.post("/v1/tasks", headers={"X-Actor-Id": "requester@mig"}, json=payload)
    assert first.status_code == 201
    assert first.json()["state"] == "AWAITING_APPROVAL"

    duplicate = client.post("/v1/tasks", headers={"X-Actor-Id": "requester@mig"}, json=payload)
    assert duplicate.json()["id"] == first.json()["id"]

    denied = client.post(f"/v1/tasks/{first.json()['id']}/approve", headers={"X-Actor-Id": "requester@mig"})
    assert denied.status_code == 403

    approved = client.post(f"/v1/tasks/{first.json()['id']}/approve", headers={"X-Actor-Id": "cfo@mig"})
    assert approved.json()["state"] == "APPROVED"

    executed = client.post(f"/v1/tasks/{first.json()['id']}/execute", headers={"X-Actor-Id": "system-orchestrator"})
    assert executed.json()["state"] == "EXECUTED"

import pytest
from fastapi.testclient import TestClient

from main import app, brain_coral_bridge, gateway, mnos_hub, shadow_core

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_bridge_rate_limit():
    # The legacy gateway uses a process-global request counter without a time window.
    # Reset the shared process counter after each integration test.
    gateway.rate_limits.clear()
    try:
        yield
    finally:
        gateway.rate_limits.clear()


def test_brain_coral_can_read_operational_status(create_verified_identity):
    identity = create_verified_identity("Brain Coral Analyst", "brain_coral")

    response = client.get("/imoxon/brain-coral/status", headers=identity["headers"])

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "CONNECTED"
    assert payload["mode"] == "READ_ONLY_INTELLIGENCE"
    assert payload["permissions"]["direct_finance_mutation"] is False
    assert payload["permissions"]["requires_execution_guard"] is True
    assert any(
        block["event_type"] == "brain_coral.operational.read.completed"
        for block in shadow_core.chain
    )


def test_brain_coral_restricted_mutation_request_fails_closed(create_verified_identity):
    identity = create_verified_identity("Brain Coral Operator", "brain_coral")

    response = client.post(
        "/imoxon/brain-coral/action-request",
        headers=identity["headers"],
        json={
            "target": "finance.release",
            "intent": "release funds directly",
            "payload": {"amount": 1000},
        },
    )

    assert response.status_code == 403
    assert "direct mutation blocked" in response.json()["detail"]
    assert any(
        block["event_type"] == "brain_coral.action.request.failed"
        for block in shadow_core.chain
    )


def test_non_brain_coral_actor_cannot_access_bridge(create_verified_identity):
    identity = create_verified_identity("Regular User", "user")

    response = client.get("/imoxon/brain-coral/status", headers=identity["headers"])

    assert response.status_code == 403
    assert "Action requires BRAIN CORAL or admin role" in response.json()["detail"]


def test_mnos_internal_sync_uses_authorized_context():
    result = mnos_hub.sync_internal_state(
        "dashboard_refresh",
        {"island": "OMADHOO", "status": "REFRESHED"},
    )

    assert result["status"] == "SYNCED"
    assert result in mnos_hub.sync_log
    assert any(
        block["event_type"] == "mnos.internal.sync.completed"
        and block["actor_id"] == "MNOS_SYSTEM"
        for block in shadow_core.chain
    )


def test_brain_coral_safe_request_is_queued(create_verified_identity):
    identity = create_verified_identity("Brain Coral Planner", "brain_coral")

    response = client.post(
        "/imoxon/brain-coral/action-request",
        headers=identity["headers"],
        json={
            "target": "ops.summary.review",
            "intent": "prepare human review pack",
            "payload": {"scope": "SALA_OMAGILI"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "QUEUED_FOR_GOVERNED_REVIEW"
    assert payload["request_id"] in brain_coral_bridge.action_requests


@pytest.mark.parametrize("target", ["procurement.order.approve", "imoxon.payment.release", "finance.refund.approve", "ops.summary.review.extra"])
def test_unknown_or_protected_action_rejected(create_verified_identity, target):
    identity = create_verified_identity("Brain Coral Reviewer", "brain_coral")
    response = client.post(
        "/imoxon/brain-coral/action-request", headers=identity["headers"],
        json={"target": target, "intent": "review", "payload": {}},
    )
    assert response.status_code == 403


@pytest.mark.parametrize("body", [{}, {"payload": {}}, {"target": "  "}])
def test_missing_target_rejected(create_verified_identity, body):
    identity = create_verified_identity("Brain Coral Reviewer", "brain_coral")
    response = client.post(
        "/imoxon/brain-coral/action-request", headers=identity["headers"], json=body,
    )
    assert response.status_code == 400

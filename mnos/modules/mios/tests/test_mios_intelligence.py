import pytest
from uuid import uuid4
from mnos.modules.mios.intelligence.agent_layer import FCEReconciliationAgent, DocumentCheckingAgent
from mnos.modules.mios.intelligence.gates import ExecutionGates
from mnos.modules.mios.services.shadow_service import MIOSShadowService
from mnos.modules.shadow.ledger import ShadowLedger

@pytest.fixture
def shadow_svc():
    from mnos.shared.execution_guard import _sovereign_context
    _sovereign_context.set({"token": "TEST-TOKEN", "actor": {"identity_id": "SYSTEM"}})
    global_shadow = ShadowLedger()
    return MIOSShadowService(global_shadow)

def test_agent_suggestions(shadow_svc):
    shipment_id = uuid4()
    agent = FCEReconciliationAgent(shadow_svc)
    result = agent.reconcile(shipment_id)

    assert result["status"] == "MATCHED"
    # Check if event was committed to shadow (via shadow_svc chain)
    assert shipment_id in shadow_svc.shipment_chains

def test_execution_gates(shadow_svc):
    gates = ExecutionGates(shadow_svc.global_shadow)

    # Allowed action
    assert gates.validate_agent_action("prepare") is True

    # Blocked action
    assert gates.validate_agent_action("bypass_customs") is False

def test_human_approval_flow(shadow_svc):
    gates = ExecutionGates(shadow_svc.global_shadow)
    shipment_id = uuid4()

    approval_id = gates.request_human_approval(shipment_id, "high_value_override", {"amount": 1000000})
    assert approval_id in gates.pending_approvals
    assert gates.pending_approvals[approval_id]["status"] == "PENDING"

def test_human_approval_short_action(shadow_svc):
    gates = ExecutionGates(shadow_svc.global_shadow)
    shipment_id = uuid4()
    # Test short action name that previously would crash deterministic UUID generation
    approval_id = gates.request_human_approval(shipment_id, "A", {"note": "short"})
    assert approval_id in gates.pending_approvals

def test_multiple_approvals_collision(shadow_svc):
    gates = ExecutionGates(shadow_svc.global_shadow)
    shipment_id = uuid4()
    action = "test_action"

    id1 = gates.request_human_approval(shipment_id, action, {"v": 1})
    id2 = gates.request_human_approval(shipment_id, action, {"v": 2})

    assert id1 != id2
    assert len(gates.pending_approvals) == 2

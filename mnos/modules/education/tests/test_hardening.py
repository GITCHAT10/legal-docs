import pytest
from mnos.core.guard import ExecutionGuard
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.core.policy import PolicyEngine

def test_execution_guard_policy_enforcement():
    ledger = ShadowLedger()
    guard = ExecutionGuard(ledger)

    def mock_action(x, **kwargs):
        return x * 2

    result = guard.execute("MOCK_ACTION", "ACTOR-001", mock_action, 10, correlation_id="CORR-101")
    assert result == 20
    assert any(entry["event_type"] == "INTENT_MOCK_ACTION" for entry in ledger.chain)
    assert any(entry["event_type"] == "RESULT_MOCK_ACTION" for entry in ledger.chain)

def test_policy_engine_rejection():
    policy = PolicyEngine()
    # Mock context missing verified_identity
    assert policy.evaluate("CERTIFY_STUDENT", {"verified_identity": False}) is False
    assert policy.evaluate("CERTIFY_STUDENT", {"verified_identity": True}) is True

import pytest
from mnos.core.governance.supervisor_gate import require_supervisor_approval, ApprovalRequired
from mnos.core.ai.engine import AiEngine
from mnos.core.ai.models import AiDecision, DecisionStatus

def test_supervisor_approval_success():
    action = "UPGRADE_VESSEL"
    operator_id = "OP-123"
    result = require_supervisor_approval(action, operator_id)

    assert result["status"] == "APPROVED"
    assert result["approved_by"] == operator_id
    assert result["action"] == action
    assert "timestamp" in result

def test_supervisor_approval_missing_operator():
    with pytest.raises(ApprovalRequired) as excinfo:
        require_supervisor_approval("ANY_ACTION", None)
    assert "requires a valid supervisor operator_id" in str(excinfo.value)

    with pytest.raises(ApprovalRequired):
        require_supervisor_approval("ANY_ACTION", "")

    with pytest.raises(ApprovalRequired):
        require_supervisor_approval("ANY_ACTION", "   ")

@pytest.mark.asyncio
async def test_ai_engine_execution_with_approval():
    engine = AiEngine()
    decision = AiDecision(
        module="routing_optimizer",
        action="UPGRADE_VESSEL",
        reasoning="High demand",
        parameters={},
        confidence_score=0.95,
        status=DecisionStatus.ELIGIBLE_FOR_REVIEW,
        trace_id="TR-123"
    )

    # Test approved path
    result = await engine.approve_and_execute_decision(decision, "SUPER-456")
    assert result["status"] == "EXECUTED"
    assert decision.status == DecisionStatus.APPROVED

    # Test blocked path (REJECTED status)
    rejected_decision = decision.model_copy()
    rejected_decision.status = DecisionStatus.REJECTED
    result_blocked = await engine.approve_and_execute_decision(rejected_decision, "SUPER-456")
    assert result_blocked["status"] == "BLOCKED"

    # Test blocked path (Missing approval)
    with pytest.raises(ApprovalRequired):
        await engine.approve_and_execute_decision(decision, "")

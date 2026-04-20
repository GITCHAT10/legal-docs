import pytest
import os
import json
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
from mnos.core.ai.models import PrestigeData, BookingData, FinanceData, DecisionStatus, AiDecision
from mnos.core.ai.engine import AiEngine
from mnos.core.governance.supervisor_gate import ApprovalRequired

@pytest.mark.asyncio
async def test_shadow_write_failure_fails_closed():
    engine = AiEngine()
    # Mock mnos_client to return failure for SHADOW_AUDIT_WRITE
    async def mock_publish(event_type, data, trace_id=None):
        if event_type == "SHADOW_AUDIT_WRITE":
            return {"status": "FAILED"}
        return {"status": "SUCCESS"}

    engine.mnos_client.publish_event = mock_publish

    prestige = [PrestigeData(journey_id="J1", origin="MLE", destination="GAN", searches_last_24h=10, conversion_rate=0.5, competitor_prices={})]
    booking = [BookingData(route_id="R1", total_capacity=100, booked_seats=50, avg_lead_time_days=1.0, cancellation_rate=0.0, last_booking_timestamp=datetime.now(timezone.utc))]

    # Cycle should return empty decisions due to fail-closed behavior on shadow failure
    output = await engine.run_optimization_cycle(prestige, booking, [])
    assert output.decisions == []
    assert "SHADOW ledger binding failed" in output.metadata["error"]

@pytest.mark.asyncio
async def test_aegis_policy_rejection():
    engine = AiEngine()
    # Create a decision that violates policy (e.g. tax keyword)
    prestige = []
    booking = []

    # Mock optimizers to only return the rejected decision
    with patch("mnos.core.ai.routing_optimizer.service.RoutingOptimizer.optimize", new_callable=AsyncMock) as mock_opt_route:
        with patch("mnos.core.ai.demand_predictor.service.DemandPredictor.predict", new_callable=AsyncMock) as mock_opt_demand:
            with patch("mnos.core.ai.revenue_optimizer.service.RevenueOptimizer.optimize", new_callable=AsyncMock) as mock_opt_rev:
                mock_opt_route.return_value = [AiDecision(
                    module="routing_optimizer",
                    action="UPDATE_TAX",
                    reasoning="Testing rejection",
                    parameters={"tax": 0.2},
                    confidence_score=0.95
                )]
                mock_opt_demand.return_value = []
                mock_opt_rev.return_value = []

                output = await engine.run_optimization_cycle(prestige, booking, [])

    assert len(output.decisions) == 1
    assert output.decisions[0].status == DecisionStatus.REJECTED
    assert "AEGIS REJECTED" in output.decisions[0].bounded_reason

@pytest.mark.asyncio
async def test_supervisor_approval_and_execute_event():
    engine = AiEngine()
    engine.mnos_client.publish_event = AsyncMock(return_value={"status": "SUCCESS"})

    decision = AiDecision(
        module="revenue_optimizer",
        action="INCREASE_PRICE",
        reasoning="High demand",
        parameters={"increase": 0.1},
        confidence_score=0.98,
        status=DecisionStatus.ELIGIBLE_FOR_REVIEW,
        trace_id="TRACE-123"
    )

    result = await engine.approve_and_execute_decision(decision, "SUPER-001")

    assert result["status"] == "EXECUTED"
    assert decision.status == DecisionStatus.APPROVED

    # Check if AI_DECISION_EXECUTE was called
    engine.mnos_client.publish_event.assert_any_call(
        event_type="AI_DECISION_EXECUTE",
        data={
            "decision": decision.model_dump(),
            "approval": result["metadata"]
        },
        trace_id="TRACE-123"
    )

@pytest.mark.asyncio
async def test_stale_decision_prevention():
    # Decisions must be freshly proposed and written to SHADOW in every cycle.
    # Our implementation generates new trace IDs if not provided, ensuring freshness.
    engine = AiEngine()
    engine.mnos_client.publish_event = AsyncMock(return_value={"status": "SUCCESS"})

    prestige = [PrestigeData(journey_id="J1", origin="MLE", destination="GAN", searches_last_24h=150, conversion_rate=0.02, competitor_prices={})]
    booking = [BookingData(route_id="R1", total_capacity=100, booked_seats=95, avg_lead_time_days=1.0, cancellation_rate=0.0, last_booking_timestamp=datetime.now(timezone.utc))]

    output1 = await engine.run_optimization_cycle(prestige, booking, [])
    output2 = await engine.run_optimization_cycle(prestige, booking, [])

    assert output1.trace_id != output2.trace_id
    # Since we have mock, we check trace_id of first decision in each
    assert output1.decisions[0].trace_id == output1.trace_id
    assert output2.decisions[0].trace_id == output2.trace_id

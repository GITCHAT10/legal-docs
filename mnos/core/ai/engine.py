import json
import os
import uuid
import logging
from typing import List, Dict, Any, Optional
from mnos.core.ai.models import PrestigeData, BookingData, FinanceData, AiOutput, AiDecision, DecisionStatus
from mnos.core.ai.routing_optimizer.service import RoutingOptimizer
from mnos.core.ai.demand_predictor.service import DemandPredictor
from mnos.core.ai.revenue_optimizer.service import RevenueOptimizer
from mnos.core.ai.policy_validator import PolicyValidator
from mnos.core.governance.supervisor_gate import require_supervisor_approval, ApprovalRequired
from mnos.shared.sdk.mnos_client import MnosClient

logger = logging.getLogger(__name__)

class AiEngine:
    """
    Orchestrates AI modules and integrates with MNOS EVENTS engine.
    """
    def __init__(self):
        self.routing_optimizer = RoutingOptimizer()
        self.demand_predictor = DemandPredictor()
        self.revenue_optimizer = RevenueOptimizer()
        self.policy_validator = PolicyValidator()
        self.mnos_client = MnosClient()

    async def run_optimization_cycle(
        self,
        prestige_data: List[PrestigeData],
        booking_data: List[BookingData],
        finance_data: List[FinanceData],
        trace_id: str = None
    ) -> AiOutput:
        if not trace_id:
            trace_id = str(uuid.uuid4())

        try:
            decisions: List[AiDecision] = []

            # Run each module
            decisions.extend(await self.routing_optimizer.optimize(prestige_data, booking_data))
            decisions.extend(await self.demand_predictor.predict(prestige_data, booking_data))
            decisions.extend(await self.revenue_optimizer.optimize(finance_data, booking_data))

            # Attach trace_id and validate against policy
            for d in decisions:
                d.trace_id = trace_id

            validated_decisions = self.policy_validator.validate_all(decisions)

            # Calculate scores (V1 stubs)
            avg_confidence = sum(d.confidence_score for d in validated_decisions) / len(validated_decisions) if validated_decisions else 0.0
            policy_compliance = len([d for d in validated_decisions if d.status != DecisionStatus.REJECTED]) / len(validated_decisions) if validated_decisions else 1.0

            output = AiOutput(
                trace_id=trace_id,
                decisions=validated_decisions,
                confidence_score=avg_confidence,
                policy_score=policy_compliance,
                advisory_only=True,
                metadata={
                    "input_counts": {
                        "prestige": len(prestige_data),
                        "booking": len(booking_data),
                        "finance": len(finance_data)
                    }
                }
            )

            # Save to decisions.json (output requirement)
            self._save_decisions(output)

            # Integrate with EVENTS engine
            await self.mnos_client.publish_event(
                event_type="AI_OPTIMIZATION_COMPLETED",
                data=output.model_dump(),
                trace_id=trace_id
            )

            return output

        except Exception as e:
            # Fail-Closed Behavior
            logger.error(f"AiEngine optimization cycle failed: {str(e)}")

            # Log failure to SHADOW
            await self.mnos_client.publish_event(
                event_type="AI_OPTIMIZATION_FAILED",
                data={"error": str(e)},
                trace_id=trace_id
            )

            # Return safe empty advisory
            empty_output = AiOutput(
                trace_id=trace_id,
                decisions=[],
                confidence_score=0.0,
                policy_score=0.0,
                advisory_only=True,
                metadata={"error": str(e)}
            )
            self._save_decisions(empty_output)
            return empty_output

    async def execute_decision_with_approval(self, decision: AiDecision, operator_id: Optional[str]) -> Dict[str, Any]:
        """
        Phase 2 implementation of L2 Supervisor Gate for state-changing actions.
        AI remains ADVISORY_ONLY; human approval required before execution.
        """
        if decision.status == DecisionStatus.REJECTED:
            # SHADOW logging for blocked cases
            await self.mnos_client.publish_event(
                event_type="SUPERVISOR_BLOCKED",
                data={
                    "decision": decision.model_dump(),
                    "reason": "Policy REJECTED status"
                },
                trace_id=decision.trace_id
            )
            return {"status": "BLOCKED", "reason": "Decision was rejected by policy gate."}

        try:
            # Mandatory human approval check
            approval_metadata = require_supervisor_approval(decision.action, operator_id)

            # SHADOW logging for approved cases
            await self.mnos_client.publish_event(
                event_type="SUPERVISOR_APPROVED",
                data={
                    "decision": decision.model_dump(),
                    "approval": approval_metadata
                },
                trace_id=decision.trace_id
            )

            return {
                "status": "APPROVED",
                "execution_ready": True,
                "metadata": approval_metadata
            }
        except ApprovalRequired as e:
            # SHADOW logging for blocked cases (missing approval)
            await self.mnos_client.publish_event(
                event_type="SUPERVISOR_BLOCKED",
                data={
                    "decision": decision.model_dump(),
                    "reason": str(e)
                },
                trace_id=decision.trace_id
            )
            raise

    def _save_decisions(self, output: AiOutput):
        """Saves decisions to decisions.json in the current working directory."""
        filepath = "decisions.json"
        with open(filepath, "w") as f:
            f.write(output.model_dump_json(indent=2))
        print(f"Decisions saved to {filepath}")

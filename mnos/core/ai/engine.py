import json
import os
import uuid
import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
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
    Orchestrates AI modules and integrates with MNOS CORE (EVENTS, SHADOW, AEGIS).
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

            # Attach trace_id
            for d in decisions:
                d.trace_id = trace_id

            validated_decisions = self.policy_validator.validate_all(decisions)

            # AEGIS Policy Compliance Score
            policy_compliance = len([d for d in validated_decisions if d.status != DecisionStatus.REJECTED]) / len(validated_decisions) if validated_decisions else 1.0
            avg_confidence = sum(d.confidence_score for d in validated_decisions) / len(validated_decisions) if validated_decisions else 0.0

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

            # 1. SHADOW Ledger Binding (Audit-First)
            # Fail closed if SHADOW write fails
            await self._bind_to_shadow(output, prestige_data, booking_data, finance_data)

            # 2. Save to decisions.json
            self._save_decisions(output)

            # 3. EVENTS Integration
            for d in output.decisions:
                await self.mnos_client.publish_event(
                    event_type="AI_DECISION_PROPOSED",
                    data={
                        "module": d.module,
                        "confidence_score": d.confidence_score,
                        "policy_score": output.policy_score,
                        "decision_payload": d.model_dump()
                    },
                    trace_id=trace_id
                )

            return output

        except Exception as e:
            # Fail-Closed Behavior
            logger.error(f"AiEngine optimization cycle failed: {str(e)}")

            await self.mnos_client.publish_event(
                event_type="AI_OPTIMIZATION_FAILED",
                data={"error": str(e)},
                trace_id=trace_id
            )

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

    async def _bind_to_shadow(self, output: AiOutput, prestige: Any, booking: Any, finance: Any):
        """Writes AI decisions to SHADOW ledger before any possible execution."""
        # Create hashes for audit integrity
        decision_hash = hashlib.sha256(output.model_dump_json().encode()).hexdigest()
        input_data = {"prestige": [p.model_dump() for p in prestige],
                      "booking": [b.model_dump() for b in booking],
                      "finance": [f.model_dump() for f in finance]}
        input_hash = hashlib.sha256(json.dumps(input_data, default=str).encode()).hexdigest()
        policy_hash = hashlib.sha256(str(PolicyValidator.PROHIBITED_KEYWORDS + PolicyValidator.PROHIBITED_EVENTS).encode()).hexdigest()

        shadow_log = {
            "trace_id": output.trace_id,
            "decision_hash": decision_hash,
            "input_hash": input_hash,
            "policy_hash": policy_hash,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "PROPOSED"
        }

        # SDK call to SHADOW
        result = await self.mnos_client.publish_event(
            event_type="SHADOW_AUDIT_WRITE",
            data=shadow_log,
            trace_id=output.trace_id
        )

        if result.get("status") != "SUCCESS":
            raise RuntimeError(f"SHADOW ledger binding failed for trace_id {output.trace_id}")

    async def approve_and_execute_decision(self, decision: AiDecision, operator_id: str) -> Dict[str, Any]:
        """
        L2 Supervisor Gate: Human approval for AI decisions.
        """
        if decision.status == DecisionStatus.REJECTED:
             return {"status": "BLOCKED", "reason": "Decision rejected by AEGIS policy."}

        try:
            # Mandatory human approval check
            approval_metadata = require_supervisor_approval(decision.action, operator_id)

            # Update status to APPROVED
            decision.status = DecisionStatus.APPROVED

            # Emit execution event
            await self.mnos_client.publish_event(
                event_type="AI_DECISION_EXECUTE",
                data={
                    "decision": decision.model_dump(),
                    "approval": approval_metadata
                },
                trace_id=decision.trace_id
            )

            return {
                "status": "EXECUTED",
                "metadata": approval_metadata
            }
        except ApprovalRequired as e:
            await self.mnos_client.publish_event(
                event_type="SUPERVISOR_BLOCKED",
                data={"decision": decision.model_dump(), "reason": str(e)},
                trace_id=decision.trace_id
            )
            raise

    def _save_decisions(self, output: AiOutput):
        """Saves decisions to decisions.json in the current working directory."""
        filepath = "decisions.json"
        with open(filepath, "w") as f:
            f.write(output.model_dump_json(indent=2))
        print(f"Decisions saved to {filepath}")

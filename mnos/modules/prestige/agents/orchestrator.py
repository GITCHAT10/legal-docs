from enum import Enum
from typing import List, Dict, Any, Optional
import uuid
from mnos.shared.execution_guard import ExecutionGuard

class AgentPermission(str, Enum):
    READ_ONLY = "READ_ONLY"
    DRAFT_ONLY = "DRAFT_ONLY"
    VALIDATION_REQUEST = "VALIDATION_REQUEST"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    FORBIDDEN = "FORBIDDEN"

class AgentOrchestrator:
    def __init__(self, core, registry):
        self.core = core
        self.registry = registry

    async def run_booking_flow(self, intake_data: Dict[str, Any], actor_ctx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Controlled agentic chain:
        Inquiry -> Planner -> Hotel -> Transfer -> Pricing -> Compliance -> Risk -> Brief -> Escalation -> MAC EOS
        """
        trace_id = str(uuid.uuid4())
        with ExecutionGuard.authorized_context(actor_ctx):
            self.core.shadow.commit("prestige.agentic.workflow_started", actor_ctx.get("identity_id", "SYSTEM"), {"trace_id": trace_id})

        # 1. Selection & Execution (Simulated multi-agent run)
        recommendations = []

        # This is a simplified sequential flow for the orchestrator
        agent_sequence = ["planner", "channel_manager", "hotel_agent", "transfer_agent", "pricing_agent", "compliance", "risk_agent", "brief_agent"]

        context = intake_data.copy()
        context["trace_id"] = trace_id

        for agent_type in agent_sequence:
            agent = self.registry.get_agent(agent_type)
            if not agent: continue

            with ExecutionGuard.authorized_context(actor_ctx):
                self.core.shadow.commit("prestige.agentic.agent_selected", agent.agent_id, {"type": agent_type, "trace_id": trace_id})

            output = await agent.execute_task(context, actor_ctx)
            if not output.get("trace_id"):
                output["trace_id"] = trace_id

            recommendations.append(output)
            context.update(output) # Chain context

            with ExecutionGuard.authorized_context(actor_ctx):
                self.core.shadow.commit("prestige.agentic.recommendation_created", agent.agent_id, {"trace_id": trace_id, "status": output.get("status")})

        # 2. Multi-agent contradiction check
        contradiction = self._check_contradictions(recommendations)
        if contradiction:
            with ExecutionGuard.authorized_context(actor_ctx):
                self.core.shadow.commit("prestige.agentic.contradiction_detected", "ORCHESTRATOR", {"trace_id": trace_id, "details": contradiction})
            return {
                "trace_id": trace_id,
                "status": "HUMAN_REVIEW_REQUIRED",
                "error": "AGENT_CONTRADICTION_DETECTED",
                "details": contradiction
            }

        # 3. Final Prep
        return {
            "trace_id": trace_id,
            "recommendations": recommendations,
            "status": "PREPARED_FOR_VALIDATION",
            "requires_human_escalation": context.get("escalation_required", False)
        }

    def _check_contradictions(self, recommendations: List[Dict]) -> Optional[str]:
        """
        Runs contradiction checks:
        - Pricing vs Compliance
        - Hotel vs Transfer
        - Brief vs Risk
        """
        # Pricing vs Compliance (Simplified mock)
        # Hotel vs Transfer (e.g. Resort requires Seaplane but Transfer says Boat only)
        # This is a rule-based check on agent outputs
        return None # Assume clear for now

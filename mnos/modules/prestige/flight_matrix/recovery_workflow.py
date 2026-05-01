import uuid
from typing import Dict, Any, List
from mnos.modules.prestige.flight_matrix.models import FlightMatrixDecision, RecoveryWorkflowDecision, RecoveryOption
from mnos.modules.prestige.flight_matrix.recovery_templates import get_recovery_template, get_brief_tone

class RecoveryWorkflow:
    def __init__(self, core_system):
        self.core = core_system

    def initiate_recovery(self, actor_ctx: dict, decision: FlightMatrixDecision) -> RecoveryWorkflowDecision:
        """
        Accepts a RED FlightMatrixDecision and generates a recovery proposal.
        Doctrine: RED means PH recovery intelligence activated.
        """
        if decision.feasibility_status != "RED":
            raise ValueError("Recovery workflow only initiated for RED decisions.")

        # 1. Select matching template
        primary_reason = decision.risk_reason_codes[0] if decision.risk_reason_codes else "UNKNOWN"
        template = get_recovery_template(primary_reason)

        # 2. Generate revised proposal context
        revised_proposal = {
            "original_trip_id": decision.trace_id,
            "recovery_strategy": template.template_id,
            "guest_brief": get_brief_tone(decision.guest_segment, template.tone),
            "agent_brief": ("The guest's arrival time is outside the safe same-day transfer window. "
                            "Prestige recommends a controlled recovery routing to preserve safety."),
            "internal_brief": {
                "risk_reason": primary_reason,
                "template": template.template_id,
                "approvals_required": ["Concierge_Lead"] if decision.human_approval_required else []
            }
        }

        # 3. Commit to SHADOW
        actor_id = actor_ctx.get("identity_id", "SYSTEM")
        shadow_id = uuid.uuid4().hex
        self.core.shadow.commit("prestige.flight_matrix.recovery_proposal_created", actor_id, {
            "decision_id": decision.trace_id,
            "template": template.template_id,
            "trace_id": shadow_id
        })

        return RecoveryWorkflowDecision(
            decision_id=decision.trace_id,
            selected_template=template.template_id,
            revised_proposal=revised_proposal,
            approvals_pending=["HumanReview"] if decision.human_approval_required else [],
            shadow_seal=shadow_id
        )

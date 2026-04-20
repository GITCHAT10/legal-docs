from typing import List
from mnos.core.ai.models import AiDecision, DecisionStatus

class PolicyValidator:
    """
    Enforces strict policy gates for AI decisions.
    """

    PROHIBITED_KEYWORDS = ["tax", "tgst", "service_charge", "mira", "ledger", "folio", "payment"]
    PROHIBITED_EVENTS = ["folio", "payment", "ledger", "execute_transaction", "bypass_policy", "fce_override"]

    def validate(self, decision: AiDecision) -> AiDecision:
        """
        Validates a single decision against policy rules.
        """
        # 1. Hard Prohibitions
        if self._check_prohibitions(decision):
            decision.status = DecisionStatus.REJECTED
            decision.bounded_reason = "Policy Violation: Attempted modification of tax logic or prohibited financial execution."
            return decision

        # 2. Confidence Thresholds (Specific to revenue_optimizer as per request)
        if decision.module == "revenue_optimizer":
            if decision.confidence_score < 0.85:
                decision.status = DecisionStatus.REJECTED
                decision.bounded_reason = "Low confidence threshold (<0.85) for revenue optimization."
            elif 0.85 <= decision.confidence_score < 0.93:
                decision.status = DecisionStatus.ADVISORY
                decision.bounded_reason = "Medium confidence (0.85-0.929): Advisory only."
            elif decision.confidence_score >= 0.93:
                decision.status = DecisionStatus.ELIGIBLE_FOR_REVIEW
                decision.bounded_reason = "High confidence (>=0.93): Eligible for policy review."
        else:
            # Default for other modules if not specified, though request focused on revenue
            decision.status = DecisionStatus.ELIGIBLE_FOR_REVIEW

        return decision

    def _check_prohibitions(self, decision: AiDecision) -> bool:
        # Check parameters for tax keywords
        param_str = str(decision.parameters).lower()
        if any(keyword in param_str for keyword in self.PROHIBITED_KEYWORDS):
            return True

        # Check action for prohibited events
        action_lower = decision.action.lower()
        if any(event in action_lower for event in self.PROHIBITED_EVENTS):
            return True

        return False

    def validate_all(self, decisions: List[AiDecision]) -> List[AiDecision]:
        return [self.validate(d) for d in decisions]

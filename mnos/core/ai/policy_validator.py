from typing import List
from mnos.core.ai.models import AiDecision, DecisionStatus

class PolicyValidator:
    """
    Enforces strict policy gates for AI decisions (AEGIS compliance).
    """

    PROHIBITED_KEYWORDS = ["tax", "tgst", "service_charge", "mira", "ledger", "folio", "payment"]
    PROHIBITED_EVENTS = ["folio", "payment", "ledger", "execute_transaction", "bypass_policy", "fce_override"]

    # AEGIS Thresholds
    CONFIDENCE_THRESHOLD = 0.90
    POLICY_SCORE_THRESHOLD = 0.95

    def validate(self, decision: AiDecision) -> AiDecision:
        """
        Validates a single decision against policy rules (AEGIS).
        """
        # 1. AEGIS HARD PROHIBITION / COMPLIANCE CHECK
        is_compliant = not self._check_prohibitions(decision)

        if not is_compliant:
            decision.status = DecisionStatus.REJECTED
            decision.bounded_reason = "AEGIS REJECTED: Prohibited action or keywords detected."
            return decision

        # 2. AEGIS CONFIDENCE THRESHOLDS
        if decision.confidence_score >= self.CONFIDENCE_THRESHOLD:
            decision.status = DecisionStatus.ELIGIBLE_FOR_REVIEW
            decision.bounded_reason = "AEGIS COMPLIANT: Eligible for supervisor review."
        elif decision.confidence_score < 0.85: # Preserving specific Rejected threshold if exists, or using AEGIS
            decision.status = DecisionStatus.REJECTED
            decision.bounded_reason = f"AEGIS REJECTED: Confidence ({decision.confidence_score}) below absolute minimum (0.85)."
        else:
            decision.status = DecisionStatus.ADVISORY
            decision.bounded_reason = f"AEGIS ADVISORY: Confidence ({decision.confidence_score}) below proposal threshold ({self.CONFIDENCE_THRESHOLD})."

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

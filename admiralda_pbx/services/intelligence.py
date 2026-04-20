from typing import Dict, Any
from admiralda_pbx.services.guardrails import guardrails

class IntelligenceEngine:
    """
    SULTHANA Persona: Hardened context analysis + predictive decision making.
    """
    def predict_action(self, context: Dict, analysis: Dict) -> str:
        intent_score = analysis.get("intent_score", 0.0)
        confidence = analysis.get("confidence", 0.0)
        voiceprint_match = context.get("voiceprint_match", 1.0) # Default to 1.0 if not provided in check

        # Enforce execution threshold rules
        if intent_score < guardrails.INTENT_MIN_SCORE:
            return "REJECT_LOW_INTENT"

        if confidence < guardrails.CONFIDENCE_MIN_SCORE:
            return "REJECT_LOW_CONFIDENCE"

        if voiceprint_match < guardrails.VOICEPRINT_MIN_MATCH:
            return "REJECT_UNVERIFIED_VOICE"

        if intent_score >= guardrails.INTENT_MIN_SCORE:
            return "INITIATE_DUAL_CONFIRMATION"

        return "CONTINUE_MONITORING"

intelligence_engine = IntelligenceEngine()

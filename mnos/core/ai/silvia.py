from typing import Dict, Any, List
from mnos.config import config
from mnos.modules.knowledge.service import knowledge_core

class SilviaEngine:
    """
    Sovereign Intelligence Engine: Answers using NEXUS operational DNA.
    Enforces confidence and intent thresholds.
    """
    def __init__(self):
        self.intent_min = config.SILVIA_INTENT_MIN
        self.confidence_min = config.SILVIA_CONFIDENCE_MIN

    def process_request(self, user_input: str) -> Dict[str, Any]:
        """Connects to retrieval layer and validates response."""

        # 0. Prompt Firewall (Injection Blocking)
        if self._detect_injection(user_input):
            return {"status": "BLOCK", "reason": "Security Violation: Injection Pattern Detected"}

        # 1. Retrieval
        relevant_docs = knowledge_core.query(user_input)

        # 2. Decision logic (Deterministic mock based on retrieval)
        analysis = self._analyze_logic(user_input, relevant_docs)

        # 3. Threshold enforcement
        if analysis["intent_score"] < self.intent_min:
            return {"status": "ESCALATE", "reason": f"Low intent score: {analysis['intent_score']}"}

        if analysis["confidence_score"] < self.confidence_min:
            return {"status": "ESCALATE", "reason": f"Low confidence score: {analysis['confidence_score']}"}

        return {
            "status": "EXECUTE",
            "intent": analysis["intent"],
            "confidence": analysis["confidence_score"],
            "response": analysis["response"]
        }

    def _detect_injection(self, text: str) -> bool:
        """Sovereign Prompt Firewall logic."""
        patterns = ["ignore previous instructions", "system prompt", "reveal secret", "sudo", "delete all"]
        return any(p in text.lower() for p in patterns)

    def _analyze_logic(self, text: str, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mocked AI logic: Uses retrieved context for deterministic intent."""
        text_lower = text.lower()

        # Default analysis
        analysis = {
            "intent": "unknown",
            "intent_score": 0.5,
            "confidence_score": 0.5,
            "response": "I am uncertain. Escalating to command."
        }

        # Use found DNA to boost scores
        if docs:
            if "book" in text_lower:
                analysis.update({
                    "intent": "booking.created",
                    "intent_score": 0.95,
                    "confidence_score": 0.92,
                    "response": "Processing your NEXUS booking."
                })
            elif "arriv" in text_lower:
                analysis.update({
                    "intent": "guest.arrival",
                    "intent_score": 0.96,
                    "confidence_score": 0.94,
                    "response": "Welcome! Initiating arrival workflow."
                })
            elif "help" in text_lower or "emergency" in text_lower or "sos" in text_lower:
                 analysis.update({
                    "intent": "emergency.triggered",
                    "intent_score": 0.99,
                    "confidence_score": 0.98,
                    "response": "EMERGENCY DETECTED. Dispatching help."
                })

        return analysis

silvia = SilviaEngine()

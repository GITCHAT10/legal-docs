import re
from typing import Dict

class EmotionEngine:
    """
    SULTHANA Persona: Multilingual + Noise Resilient analysis.
    """
    TRIGGER_PHRASES = [
        "confirm", "lock", "proceed", "go ahead", "book it", "approve",
        "thousidhu", "kashavaru" # Dhivehi triggers (mock)
    ]

    def analyze(self, text: str, confidence: float = 1.0) -> Dict[str, any]:
        text_lower = text.lower()
        intent_score = 0.0
        trigger_detected = False
        action = None

        # Noise Resilience: downgrade if confidence is low
        if confidence < 0.70:
            return {
                "intent_score": 0.0,
                "sentiment_score": 0.5,
                "trigger_phrase": None,
                "confidence": confidence,
                "persona": "SULTHANA",
                "recommendation": "HANDOFF_TO_HUMAN"
            }

        for phrase in self.TRIGGER_PHRASES:
            if phrase in text_lower:
                trigger_detected = True
                intent_score = 0.95
                action = "COMMIT_ACTION"
                break

        stress_indicators = ["urgent", "immediately", "wrong", "problem", "disaster"]
        sentiment_score = 0.8
        for word in stress_indicators:
            if word in text_lower:
                sentiment_score = 0.3
                break

        return {
            "intent_score": intent_score,
            "sentiment_score": sentiment_score,
            "trigger_phrase": action if trigger_detected else None,
            "confidence": confidence,
            "persona": "SULTHANA",
            "recommendation": "CONTINUE"
        }

emotion_engine = EmotionEngine()

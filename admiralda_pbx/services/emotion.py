import re
from typing import Dict

class EmotionEngine:
    """
    SULTHANA Persona: Stress / sentiment / intent detection.
    """
    TRIGGER_PHRASES = [
        "confirm", "lock", "proceed", "go ahead", "book it", "approve"
    ]

    def analyze(self, text: str) -> Dict[str, any]:
        text_lower = text.lower()
        intent_score = 0.0
        trigger_detected = False
        action = None

        for phrase in self.TRIGGER_PHRASES:
            if phrase in text_lower:
                trigger_detected = True
                intent_score = 0.95
                action = "COMMIT_ACTION"
                break

        stress_indicators = ["urgent", "immediately", "wrong", "problem", "disaster"]
        sentiment_score = 0.8 # Default 'calm'
        for word in stress_indicators:
            if word in text_lower:
                sentiment_score = 0.3 # 'stressed'
                break

        return {
            "intent_score": intent_score,
            "sentiment_score": sentiment_score,
            "trigger_phrase": action if trigger_detected else None,
            "confidence": 0.91 if trigger_detected else 0.5,
            "persona": "SULTHANA"
        }

emotion_engine = EmotionEngine()

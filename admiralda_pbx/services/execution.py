from typing import Dict

class ExecutionEngine:
    """
    ADMIRALDA PBX: Handles internal PBX actions with guardrails.
    """
    def handle_action(self, action: str, call_id: str, analysis: Dict) -> Dict:
        if action == "REJECT_LOW_INTENT":
            whisper = "⚠️ Intent score too low for auto-execution. Manual review required."
            if analysis.get("sentiment_score", 1.0) < 0.5:
                whisper = "⚠️ Guest stressed — suggest empathetic de-escalation."
            return {
                "whisper": whisper,
                "execution_status": "BLOCKED"
            }

        if action == "REJECT_LOW_CONFIDENCE":
            return {
                "whisper": "⚠️ Confidence threshold not met. Ask for verbal clarification.",
                "execution_status": "BLOCKED"
            }

        if action == "REJECT_UNVERIFIED_VOICE":
            return {
                "whisper": "❌ Voiceprint match failed. Potential identity risk.",
                "execution_status": "BLOCKED"
            }

        if action == "INITIATE_DUAL_CONFIRMATION":
            return {
                "whisper": "🔗 Intent verified. Triggering WhatsApp/SMS confirmation flow.",
                "execution_status": "PENDING_CONFIRMATION",
                "ui_action": "START_DUAL_AUTH"
            }

        return {"whisper": None, "execution_status": "MONITORING"}

execution_engine = ExecutionEngine()

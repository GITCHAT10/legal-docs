from typing import List, Dict, Any
from mnos.core.asi.silvia import silvia

class SilviaUiBinder:
    """
    SALA-OS SILVIA Integration.
    Injects predictive recommendations and reasoning traces into the UI.
    Display: RIGHT_PANEL_ALERTS
    """
    def __init__(self):
        self.display_location = "RIGHT_PANEL_ALERTS"

    def get_ui_recommendations(self, context_query: str) -> Dict[str, Any]:
        """Fetches recommendations for the UI, requiring reasoning trace."""
        decision = silvia.process_request(context_query)

        # Enforce Stage 6+ requirement: Reasoning Trace
        if "shadow_reasoning_trace" not in decision:
            raise RuntimeError("SALA-SILVIA: Reasoning trace mandatory for UI injection. Blocked.")

        print(f"[SALA-SILVIA] Injecting alert into {self.display_location}")
        return {
            "alert": decision.get("response"),
            "intent": decision.get("intent"),
            "trace": decision.get("shadow_reasoning_trace"),
            "confidence": decision.get("confidence")
        }

silvia_ui = SilviaUiBinder()

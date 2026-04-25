from typing import Dict, Any
from mnos.shared.execution_guard import guard
from mnos.modules.fce.service import fce

class ReconAuthority:
    """
    RECON Sensing Layer (Singularity Core).
    Sensors are detectors only. Reactions are governed by FCE/ExecutionGuard.
    """
    def handle_detection(self, source: str, threat_level: int, metadata: Dict[str, Any], session_context: Dict[str, Any]):
        """Binds RECON detection to the sovereign core."""

        def evaluate_and_react(payload):
            # Reaction policy: block entry if TL > 3
            action = "OBSERVE"
            if payload["threat_level"] > 3:
                action = "RESTRICT_ENTRY"

            return {
                "detection_source": payload["source"],
                "threat_level": payload["threat_level"],
                "policy": "FORTRESS_ROE_V1",
                "chosen_action": action,
                "safe_exit_status": "ENABLED"
            }

        # Guarded Execution: Reality -> Signed Event -> Execution Guard -> FCE
        return guard.execute_sovereign_action(
            action_type="recon.detection.processed",
            payload={
                "source": source,
                "threat_level": threat_level,
                "metadata": metadata,
                "objective_code": "SEC-NEXUS-01"
            },
            session_context=session_context,
            execution_logic=evaluate_and_react
        )

recon = ReconAuthority()

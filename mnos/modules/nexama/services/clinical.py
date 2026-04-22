from typing import Dict, Any, List
import uuid
import datetime
from mnos.core.ai.silvia import silvia
from mnos.shared.sdk.client import mnos_client

class ClinicalService:
    async def create_encounter(self, encounter_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a clinical encounter with SILVIA AI diagnostic support,
        Safety Guardrails, and Island Logistics.
        """
        clinical_notes = encounter_data.get("clinical_notes", "")
        ai_analysis = silvia.process_request(clinical_notes)

        # 1. "AI Suggestion Only" Guardrail
        diagnostics = {
            "ai_intent": ai_analysis.get("intent"),
            "ai_confidence": ai_analysis.get("confidence"),
            "ai_suggestions": ai_analysis.get("response"),
            "status": "SUGGESTION_ONLY" # Enforced: Cannot finalize diagnosis
        }

        # 2. High-Risk Override System
        risk_level = "NORMAL"
        emergency_trigger = None

        notes_lower = clinical_notes.lower()
        high_risk_keywords = ["stroke", "cardiac", "heart attack", "unconscious", "heavy bleeding"]
        if any(kw in notes_lower for kw in high_risk_keywords):
            risk_level = "EMERGENCY"
            emergency_trigger = "HIGH_RISK_OVERRIDE"

        # 3. Island Logistics: Transport-Aware Priority
        logistics = self._calculate_island_logistics(encounter_data, risk_level)

        encounter_id = f"ENC-{uuid.uuid4()}"

        result = {
            "id": encounter_id,
            "status": "ACTIVE",
            "risk_level": risk_level,
            "is_ai_suggestion": True,
            "diagnostics": diagnostics,
            "emergency_trigger": emergency_trigger,
            "logistics": logistics,
            "metadata": {
                "source": "NEXAMA_CLINICAL_ASI",
                "requires_human_signature": True
            }
        }

        # 4. Trigger Emergency Events if necessary
        if risk_level == "EMERGENCY":
            await mnos_client.publish_event("nexama.emergency.triggered", result)
            if logistics.get("transfer_required"):
                await mnos_client.publish_event("nexama.transport.evac_requested", {
                    "encounter_id": encounter_id,
                    "priority": "CRITICAL",
                    "mode": logistics.get("recommended_mode")
                })

        return result

    def _calculate_island_logistics(self, data: Dict[str, Any], risk_level: str) -> Dict[str, Any]:
        """
        Maldives-aware logistics engine: Sea state, travel time, night/day constraints.
        """
        # Mocking environment factors for Maldives context
        current_time = datetime.datetime.utcnow().hour
        is_night = current_time > 18 or current_time < 6
        sea_state = data.get("sea_state", "CALM") # CALM, ROUGH, SEVERE

        transfer_required = risk_level == "EMERGENCY"
        recommended_mode = "BOAT"

        if transfer_required:
            if is_night:
                recommended_mode = "SEA_AMBULANCE" # Seaplanes don't fly at night
            elif sea_state == "SEVERE":
                recommended_mode = "AIR_EVAC" # Boats too risky
            else:
                recommended_mode = "SPEEDBOAT"

        return {
            "transfer_required": transfer_required,
            "recommended_mode": recommended_mode,
            "constraints": {
                "is_night": is_night,
                "sea_state": sea_state
            }
        }

clinical_service = ClinicalService()

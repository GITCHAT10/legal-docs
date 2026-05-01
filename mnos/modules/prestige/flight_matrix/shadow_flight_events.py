from typing import Dict, Any

class ShadowFlightEvents:
    """
    Utility to standardize flight matrix SHADOW event payloads.
    """
    @staticmethod
    def dataset_imported(version: str, count: int):
        return {
            "event_type": "prestige.flight_matrix.dataset_imported",
            "version": version,
            "record_count": count
        }

    @staticmethod
    def feasibility_decision(decision_id: str, status: str, reasons: list):
        return {
            "event_type": f"prestige.flight_matrix.{status.lower()}_decision",
            "decision_id": decision_id,
            "status": status,
            "risk_codes": reasons
        }

    @staticmethod
    def recovery_proposal(decision_id: str, template: str):
        return {
            "event_type": "prestige.flight_matrix.recovery_proposal_created",
            "decision_id": decision_id,
            "template_id": template
        }

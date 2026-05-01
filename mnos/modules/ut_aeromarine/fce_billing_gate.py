from mnos.modules.ut_aeromarine.mission_schema import UTAMMission, MissionStatus
import uuid

class FCEBillingGate:
    """
    UT AEROMARINE FCE Billing Gate.
    Ensures no commercial billing occurs without a forensics-sealed SHADOW trace.
    """
    def __init__(self, fce, shadow):
        self.fce = fce
        self.shadow = shadow

    def release_billing(self, mission: UTAMMission) -> dict:
        # Rule: No billing for non-commercial or non-billable missions
        if not mission.commercial_billable:
            return {"status": "NON_BILLABLE", "reason": "Operational/Emergency Mission"}

        # Rule: Billing remains blocked until mission is SHADOW_SEALED
        if mission.status != MissionStatus.SHADOW_SEALED:
            raise RuntimeError(f"FAIL CLOSED: Billing blocked. Mission status {mission.status.value} is not SHADOW_SEALED")

        # Rule: Missing SHADOW trace ID
        if not mission.shadow_trace_id:
            raise RuntimeError("FAIL CLOSED: Missing SHADOW trace ID for billable mission")

        # Generate FCE settlement
        # Assume base_price is stored in metadata or payload
        # For simulation, use a default rate if not specified
        base_rate = 150.0
        invoice = self.fce.finalize_invoice(base_rate, "TOURISM") # Using TOURISM context for billing rules

        mission.status = MissionStatus.BILLING_RELEASED

        return {
            "mission_id": mission.mission_id,
            "invoice": invoice,
            "status": "BILLING_RELEASED"
        }

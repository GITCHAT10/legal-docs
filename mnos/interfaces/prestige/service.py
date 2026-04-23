from typing import Dict, Any
from sqlalchemy.orm import Session
from mnos.shared.sdk.mnos_client import mnos_client
import uuid

class PrestigeBookingService:
    def __init__(self, db: Session):
        self.db = db

    def create_booking_intent(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        PRESTIGE layer: captures intent, then commits to MNOS.
        """
        trace_id = f"PRESTIGE-{uuid.uuid4().hex}"

        # 1. Commit booking to MNOS CORE (which handles INN for rooms and AQUA for transfers)
        mnos_response = mnos_client.commit_booking(booking_data, trace_id=trace_id)

        # 2. Open Folio in FCE (Financial Control Engine)
        folio = mnos_client.open_folio(
            reservation_id=mnos_response["reservation_id"],
            trace_id=f"FOLIO-{trace_id}"
        )

        # 3. Commit Evidence to SHADOW
        evidence = mnos_client.commit_evidence(
            trace_id=trace_id,
            payload={
                "intent": booking_data,
                "mnos_response": mnos_response,
                "folio_id": folio["id"]
            }
        )

        return {
            "status": "committed",
            "reservation_id": mnos_response["reservation_id"],
            "folio_id": folio["id"],
            "trace_id": trace_id,
            "shadow_id": evidence["id"]
        }

prestige_service = PrestigeBookingService

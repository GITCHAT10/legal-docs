import hashlib
import json
from datetime import datetime, UTC
from typing import Optional, Dict, List

class RoomRaccoonAdapter:
    """
    RoomRaccoon PMS Adapter for UHA
    - Bidirectional sync: PMS events -> training triggers
    - SHADOW cryptographic audit of PMS-LMS interactions
    """

    def __init__(self, core, education_engine):
        self.core = core
        self.edu = education_engine

    def handle_pms_webhook(self, event_type: str, payload: Dict):
        """
        Processes inbound events from RoomRaccoon PMS.
        """
        # Anonymize guest data for PDPA compliance
        if "guest_id" in payload:
            guest_id = payload.pop("guest_id")
            payload["guest_hash"] = hashlib.sha256(guest_id.encode()).hexdigest()[:16]

        # Trigger training based on reservation complexity
        if event_type == "reservation.created":
            self._process_reservation_trigger(payload)

        # Audit to SHADOW
        from mnos.shared.execution_guard import _sovereign_context
        token = _sovereign_context.set({"token": "PMS-WEBHOOK", "actor": {"identity_id": "SYSTEM", "system_override": True}})
        try:
            self.core.shadow.commit(
                f"pms.roomraccoon.{event_type}",
                "SYSTEM",
                payload
            )
        finally:
            _sovereign_context.reset(token)

        return {"status": "PROCESSED", "event": event_type}

    def _process_reservation_trigger(self, reservation: Dict):
        """
        Auto-assign training modules based on guest tier or stay length.
        """
        assigned_staff = reservation.get("assigned_staff_id")
        if not assigned_staff:
            return

        # Rule: VIP Guest -> Luxury Service Protocol
        if reservation.get("guest_tier") in ["PLATINUM", "VVIP"]:
            self.edu.enroll(
                {"identity_id": "SYSTEM", "device_id": "PMS-ADAPTER", "system_override": True},
                {"course_id": "L2-LUXURY-PROTOCOL", "student_id": assigned_staff}
            )

        # Rule: Long Stay -> Guest Retention Strategy
        if reservation.get("nights", 0) > 7:
            self.edu.enroll(
                {"identity_id": "SYSTEM", "device_id": "PMS-ADAPTER", "system_override": True},
                {"course_id": "L3-RETENTION-STRATEGY", "student_id": assigned_staff}
            )

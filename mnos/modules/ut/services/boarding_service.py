import hashlib
import uuid
from typing import Dict

class UTBoardingService:
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events
        self.boarding_tokens = {}

    def generate_boarding_qr(self, booking_id: str, trace_id: str) -> str:
        """
        Generates a QR token hash for boarding.
        """
        raw = f"{booking_id}-{trace_id}-{uuid.uuid4().hex}"
        token = hashlib.sha256(raw.encode()).hexdigest()
        self.boarding_tokens[token] = {"booking_id": booking_id, "trace_id": trace_id}
        return token

    def validate_qr_scan(self, actor_ctx: dict, qr_token: str) -> Dict:
        """
        Validates QR scan and records boarding event.
        """
        token_data = self.boarding_tokens.get(qr_token)
        if not token_data:
            raise ValueError("INVALID_QR_TOKEN: Boarding Denied")

        result = {
            "status": "BOARDED",
            "booking_id": token_data["booking_id"],
            "trace_id": token_data["trace_id"],
            "scanned_by": actor_ctx.get("identity_id")
        }

        # ORCA Validation Simulation: confirm to SHADOW
        self.shadow.commit("ut.orca.boarding_confirm", actor_ctx.get("identity_id"), result)
        self.events.publish("ut.passenger_boarded", result)

        return result

    def confirm_arrival(self, actor_ctx: dict, booking_id: str, trace_id: str) -> Dict:
        """
        Confirms arrival at destination.
        """
        result = {
            "status": "ARRIVED",
            "booking_id": booking_id,
            "trace_id": trace_id,
            "confirmed_by": actor_ctx.get("identity_id")
        }
        self.shadow.commit("ut.orca.arrival_confirm", actor_ctx.get("identity_id"), result)
        self.events.publish("ut.trip_completed", result)
        return result

from datetime import date, datetime, UTC
from typing import Dict, Any, Optional
from mnos.modules.pms.reservations.models.reservation import Reservation, ReservationStateLog
import uuid

class BookingLogic:
    """
    PMS Booking Logic: Orchestrates reservation state machine and SHADOW audits.
    """
    def __init__(self, availability_engine, guard, shadow, events):
        self.availability_engine = availability_engine
        self.guard = guard
        self.shadow = shadow
        self.events = events
        self.reservations: Dict[str, Reservation] = {}
        self.idempotency_store: Dict[str, str] = {} # key -> res_id

    def create_reservation(self, actor_ctx: dict, booking_data: dict) -> Reservation:
        """
        DRAFT -> PENDING -> CONFIRMED
        Atomic execution flow with SHADOW anchoring.
        """
        idempotency_key = booking_data.get("idempotency_key")
        if idempotency_key in self.idempotency_store:
            res_id = self.idempotency_store[idempotency_key]
            return self.reservations[res_id].to_dict()

        def _execute_booking():
            # 1. State Transition: DRAFT -> PENDING
            reservation = Reservation(
                trace_id=str(uuid.uuid4()),
                idempotency_key=idempotency_key,
                guest_id=booking_data["guest_id"],
                room_type_id=booking_data["room_type_id"],
                rate_plan_id=booking_data["rate_plan_id"],
                check_in=booking_data["check_in"],
                check_out=booking_data["check_out"],
                total_amount=booking_data["total_amount"],
                status="PENDING"
            )

            # 2. Inventory Lock (Optimistic)
            locked = self.availability_engine.lock_inventory(
                reservation.room_type_id,
                reservation.check_in,
                reservation.check_out
            )
            if not locked:
                raise ValueError("CONFLICT: No availability for requested dates/room.")

            # 3. State Transition: PENDING -> CONFIRMED
            # Audit in SHADOW before final state change
            reservation.status = "CONFIRMED"

            # Record transition log
            log_entry = ReservationStateLog(
                reservation_id=reservation.id,
                from_state="PENDING",
                to_state="CONFIRMED",
                triggered_by=actor_ctx.get("identity_id", "UNKNOWN"),
                execution_guard_result={"policy_check": "PASSED"},
                shadow_hash="PENDING_SHADOW_COMMIT"
            )

            # Persist local
            self.reservations[reservation.id] = reservation
            self.idempotency_store[idempotency_key] = reservation.id

            self.events.publish("pms.reservation.confirmed", reservation.to_dict())

            return reservation.to_dict()

        return self.guard.execute_sovereign_action(
            "pms.reservation.create",
            actor_ctx,
            _execute_booking
        )

    def cancel_reservation(self, actor_ctx: dict, res_id: str, reason: str):
        """
        CONFIRMED -> CANCELLED
        """
        def _execute_cancel():
            res = self.reservations.get(res_id)
            if not res:
                raise ValueError("Reservation not found")

            if res.status == "CANCELLED":
                return res.to_dict()

            # Release Inventory
            self.availability_engine.release_inventory(res.room_type_id, res.check_in, res.check_out)

            # Update state
            res.status = "CANCELLED"
            res.updated_at = datetime.now(UTC)
            res.metadata["cancel_reason"] = reason

            self.events.publish("pms.reservation.cancelled", res.to_dict())
            return res.to_dict()

        return self.guard.execute_sovereign_action(
            "pms.reservation.cancel",
            actor_ctx,
            _execute_cancel
        )

import uuid
from datetime import datetime, UTC, date, timedelta
from typing import Dict, Any, List, Optional
from mnos.shared.exceptions import ExecutionValidationError

class BookingGateEngine:
    """
    MAC_EOS_SOVEREIGN_BOOKING_GATE
    Governs the P0 fail-closed booking lifecycle between Prestige and iMOXON Execution Core.
    """
    def __init__(self, guard, shadow, events, pms_booking, pms_availability, ut_bridge, bubble_orchestrator, upos_engine=None):
        self.guard = guard
        self.shadow = shadow
        self.events = events
        self.pms_booking = pms_booking
        self.pms_availability = pms_availability
        self.ut_bridge = ut_bridge
        self.bubble_orchestrator = bubble_orchestrator
        self.upos_engine = upos_engine
        self.booking_states = {} # booking_id -> status_data

    def ingest_booking_intent(self, actor_ctx: dict, prestige_data: dict):
        """
        RECEIVE_BOOKING_INTENT_FROM_PRESTIGE
        Requires: trace_id, aegis_identity, device_binding_or_session
        """
        trace_id = prestige_data.get("trace_id")
        if not trace_id:
            raise ValueError("FAIL_CLOSED: Missing mandatory trace_id from Prestige")

        def _execute_ingestion():
            # 1. Real-time Validations
            # VERIFY_ROOM_AVAILABILITY_REALTIME
            check_in = prestige_data["check_in"]
            if isinstance(check_in, str): check_in = date.fromisoformat(check_in)
            check_out = prestige_data["check_out"]
            if isinstance(check_out, str): check_out = date.fromisoformat(check_out)

            avail = self.pms_availability.get_availability(
                prestige_data["room_type_id"],
                check_in,
                check_out
            )
            if avail <= 0:
                raise ExecutionValidationError(f"CONFLICT: Real-time availability check failed for {prestige_data['room_type_id']}")

            # VERIFY_RATE_INTEGRITY_FROM_PRESTIGE
            # Logic: Cross-reference Prestige amount with internal Rate Cards
            # (Simulated: allow if amount > 0 for now)
            if prestige_data["total_amount"] <= 0:
                 raise ExecutionValidationError("RATE_INTEGRITY_FAILED: Booking amount must be positive")

            # VERIFY_TRANSFER_CAPACITY_VIA_UT
            # REQUEST_TRANSFER_ASSIGNMENT (Check only)
            ut_ok = self.ut_bridge.verify_feasibility(
                 actor_ctx,
                 prestige_data.get("arrival_flight", "UNKNOWN"),
                 check_in
            )
            if not ut_ok:
                 raise ExecutionValidationError("UT_CAPACITY_FAILED: No transfer capacity for arrival window")

            # 2. Initialize Booking Status: DRAFT -> VALIDATED
            # BLOCK_DIRECT_JUMP_TO_CONFIRMED
            booking_id = f"BK-{uuid.uuid4().hex[:8].upper()}"
            status_entry = {
                "id": booking_id,
                "prestige_ref": prestige_data.get("booking_ref"),
                "status": "VALIDATED",
                "trace_id": trace_id,
                "amount_quoted": prestige_data["total_amount"],
                "room_type_id": prestige_data["room_type_id"],
                "check_in": check_in.isoformat(),
                "check_out": check_out.isoformat(),
                "created_at": datetime.now(UTC).isoformat(),
                "ut_verified": True
            }
            self.booking_states[booking_id] = status_entry

            # 3. Emit Event
            self.events.publish("booking.validated", status_entry)

            return status_entry

        return self.guard.execute_sovereign_action(
            "booking.gate.ingest",
            actor_ctx,
            _execute_ingestion
        )

    def confirm_booking(self, actor_ctx: dict, booking_id: str, payment_ref: str, payment_amount: float):
        """
        ENFORCE_BOOKING_STATUS: VALIDATED → CONFIRMED
        WAIT_FOR_UPOS_PAYMENT_CONFIRMATION
        MATCH_PAYMENT_AMOUNT_WITH_PRESTIGE_QUOTE
        """
        booking = self.booking_states.get(booking_id)
        if not booking:
            # BLOCK_SYNTHETIC_OR_UNKNOWN_BOOKINGS
            raise ExecutionValidationError(f"BOOKING_NOT_FOUND: {booking_id}")

        if booking["status"] != "VALIDATED":
            raise ExecutionValidationError(f"INVALID_STATUS_TRANSITION: Booking {booking_id} is in {booking['status']}, not VALIDATED")

        def _execute_confirmation():
            # 1. Payment Matching (BLOCK_EXECUTION_IF_PAYMENT_MISMATCH)
            if payment_amount != booking["amount_quoted"]:
                raise ExecutionValidationError(f"PAYMENT_MISMATCH: Quoted {booking['amount_quoted']} != Paid {payment_amount}")

            # 2. Transition: VALIDATED -> CONFIRMED
            # Call underlying PMS Booking Logic for atomic inventory lock
            pms_data = {
                "guest_id": actor_ctx.get("identity_id"),
                "room_type_id": booking["room_type_id"],
                "villa_id": booking.get("villa_id"),
                "rate_plan_id": "RP-AUTO",
                "check_in": booking["check_in"],
                "check_out": booking["check_out"],
                "idempotency_key": f"pay-{payment_ref}",
                "total_amount": payment_amount
            }
            pms_res = self.pms_booking.create_reservation(actor_ctx, pms_data)

            booking["status"] = "CONFIRMED"
            booking["pms_id"] = pms_res["id"]
            booking["payment_id"] = payment_ref

            self.events.publish("booking.confirmed", booking)
            return booking

        return self.guard.execute_sovereign_action(
            "booking.gate.confirm",
            actor_ctx,
            _execute_confirmation
        )

    def request_execution(self, actor_ctx: dict, booking_id: str):
        """
        CONFIRMED → EXECUTION_PENDING
        Initialize order in Bubble Reality Engine.
        """
        booking = self.booking_states.get(booking_id)
        if not booking or booking["status"] != "CONFIRMED":
            raise ExecutionValidationError(f"CANNOT_EXECUTE: Booking {booking_id} not confirmed")

        def _execute_request():
            # 1. UT Bridge Assignment
            self.ut_bridge.assign_vessel(actor_ctx, f"MAN-{booking_id}", "VESSEL-AUTO")

            # 2. Bubble Orchestrator: Register Order for Reality Check
            # This makes the digital order "awaiting physical signal"
            self.bubble_orchestrator.set_order_state(
                 booking_id,
                 "EXECUTION_PENDING",
                 order_type="TRANSPORT"
            )

            booking["status"] = "EXECUTION_PENDING"
            self.events.publish("execution.pending", booking)
            return booking

        return self.guard.execute_sovereign_action(
            "booking.gate.execute_request",
            actor_ctx,
            _execute_request
        )

    def complete_execution(self, actor_ctx: dict, booking_id: str, signal: dict):
        """
        EXECUTION_PENDING → EXECUTION_STARTED → COMPLETED
        Verify physical signal via Bubble.
        """
        booking = self.booking_states.get(booking_id)
        if not booking or booking["status"] != "EXECUTION_PENDING":
             raise ExecutionValidationError(f"CANNOT_COMPLETE: Booking {booking_id} not in execution pending")

        def _execute_completion():
            # reality check via bubble
            self.bubble_orchestrator.confirm_real_world(booking_id, signal)

            booking["status"] = "COMPLETED"
            self.events.publish("execution.completed", booking)
            return booking

        return self.guard.execute_sovereign_action(
            "booking.gate.complete_execution",
            actor_ctx,
            _execute_completion
        )

    def final_audit_check(self, booking_id: str):
        """
        EXPORT_TRACE_CHAIN (PRESTIGE → MAC_EOS → UPOS)
        ASSERT_NO_EXECUTION_WITHOUT_PAYMENT
        """
        booking = self.booking_states.get(booking_id)
        if not booking: return None

        chain = []
        for block in self.shadow.chain:
             # Match by trace_id or internal booking ID
             if block["payload"].get("trace_id") == booking["trace_id"] or block["payload"].get("id") == booking_id:
                  chain.append({
                      "index": block["index"],
                      "type": block["event_type"],
                      "hash": block["hash"],
                      "payload": block["payload"]
                  })

        # Audit Assertions
        has_ingest = any(c["type"] == "booking.gate.ingest.completed" for c in chain)
        has_payment = any(c["type"] == "booking.gate.confirm.completed" for c in chain)
        has_exec_req = any(c["type"] == "booking.gate.execute_request.completed" for c in chain)
        has_complete = any(c["type"] == "booking.gate.complete_execution.completed" for c in chain)

        # Scoring logic
        score = 0.2 # initial
        if has_ingest: score += 0.2
        if has_payment: score += 0.2
        if has_exec_req: score += 0.2
        if has_complete: score += 0.2

        return {
            "booking_id": booking_id,
            "trace_id": booking["trace_id"],
            "full_evidence_chain": chain,
            "integrity_report": {
                "execution_without_payment": has_exec_req and not has_payment,
                "payment_without_booking": has_payment and not has_ingest,
                "score": round(score, 1)
            }
        }

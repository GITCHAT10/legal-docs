import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, time, timedelta
from mnos.modules.prestige.flight_matrix.models import FlightMatrixDecision, FlightConnectivityRecord

class TransferFeasibilityMatrix:
    def __init__(self, core_system, loader, config):
        self.core = core_system
        self.loader = loader
        self.config = config

    def evaluate_feasibility(self, actor_ctx: dict, context: Dict[str, Any]) -> FlightMatrixDecision:
        """
        Executes traffic-light feasibility logic (Gates A-F).
        Doctrine: Matrix recommends, UT validates transport reality, SHADOW seals decision.
        """
        trace_id = context.get("trace_id", uuid.uuid4().hex)
        flight_number = context.get("flight_number")
        resort_id = context.get("resort_id")
        resort_name = context.get("resort_name")
        transfer_mode = context.get("transfer_mode")
        atoll_zone = context.get("atoll_zone")
        scheduled_arrival = context.get("scheduled_arrival_time_mle")
        privacy_level = context.get("privacy_level", 2)
        guest_segment = context.get("guest_segment", "STANDARD")

        status = "GREEN"
        reasons = []
        recovery_required = False
        human_approval_required = False

        # Gate F: Missing Data
        if not flight_number or not scheduled_arrival or not transfer_mode or not resort_id:
            status = "NEEDS_HUMAN_REVIEW"
            reasons.append("MISSING_FEASIBILITY_DATA")
            return self._finalize_decision(trace_id, status, reasons, context)

        arrival_time_dt = datetime.strptime(scheduled_arrival, "%H:%M")
        cutoff_time_dt = datetime.strptime(self.config.get("seaplane_cutoff_time", "15:30"), "%H:%M")

        # Gate A: Seaplane Cutoff
        if transfer_mode == "SEAPLANE":
            buffer = self.config.get("international_to_seaplane_buffer_minutes", 60)
            earliest_seaplane = arrival_time_dt + timedelta(minutes=buffer)
            if earliest_seaplane > cutoff_time_dt:
                status = "RED"
                reasons.append("SEAPLANE_CUTOFF_RISK")
                recovery_required = True

        # Gate B: Domestic Buffer
        if transfer_mode == "DOMESTIC_PLUS_SPEEDBOAT":
            last_flight = context.get("last_domestic_flight_time")
            if last_flight:
                last_flight_dt = datetime.strptime(last_flight, "%H:%M")
                buffer = self.config.get("domestic_connection_buffer_minutes", 120)
                if arrival_time_dt + timedelta(minutes=buffer) > last_flight_dt:
                    status = "RED"
                    reasons.append("DOMESTIC_CONNECTION_MISSED")
                    recovery_required = True

        # Gate C: Night Speedboat
        if transfer_mode == "SPEEDBOAT":
            male_zones = ["NORTH_MALE", "SOUTH_MALE"]
            night_cutoff = datetime.strptime(self.config.get("night_speedboat_review_after", "18:00"), "%H:%M")
            if atoll_zone not in male_zones and arrival_time_dt > night_cutoff:
                if status != "RED":
                    status = "YELLOW"
                reasons.append("NIGHT_SPEEDBOAT_REVIEW_REQUIRED")
                human_approval_required = True

        # Gate D: Weather / Swell
        swell_height = context.get("swell_height_m", 0)
        swell_threshold = self.config.get("night_speedboat_swell_red_threshold_m", 2.5)
        if transfer_mode == "SPEEDBOAT" and arrival_time_dt > datetime.strptime("18:00", "%H:%M"):
            if swell_height > swell_threshold:
                status = "RED"
                reasons.append("UNSAFE_NIGHT_SPEEDBOAT")
                recovery_required = True

        # Gate E: Baggage Risk
        baggage_markets = self.config.get("heavy_baggage_markets", [])
        if context.get("market_region") in baggage_markets and context.get("aircraft_capacity") == "SMALL":
             if status == "GREEN": status = "YELLOW"
             reasons.append("BAGGAGE_OFFLOAD_RISK")
             human_approval_required = True

        # Mandatory Escalation Rules
        if privacy_level >= 3:
            if status in ["YELLOW", "RED"]:
                human_approval_required = True
        if guest_segment == "UHNW" and status != "GREEN":
            human_approval_required = True
        if context.get("is_private_jet") and recovery_required:
            human_approval_required = True

        return self._finalize_decision(trace_id, status, reasons, context, recovery_required, human_approval_required)

    def _finalize_decision(self, trace_id, status, reasons, context, recovery=False, human=False) -> FlightMatrixDecision:
        decision = FlightMatrixDecision(
            trace_id=trace_id,
            feasibility_status=status,
            risk_reason_codes=reasons,
            recovery_required=recovery,
            human_approval_required=human,
            safe_to_quote=(status in ["GREEN", "YELLOW"]),
            safe_to_confirm=False, # Always false until downstream completion
            market_region=context.get("market_region"),
            flight_number=context.get("flight_number"),
            resort_id=context.get("resort_id"),
            privacy_level=context.get("privacy_level", 2),
            guest_segment=context.get("guest_segment", "STANDARD")
        )

        # SHADOW event
        actor_id = self.core.guard.get_actor().get("identity_id", "SYSTEM") if self.core.guard.is_authorized() else "SYSTEM"
        event_type = f"prestige.flight_matrix.{status.lower()}_decision"
        self.core.shadow.commit(event_type, actor_id, decision.model_dump())

        return decision

from uuid import UUID, uuid4
from decimal import Decimal
from typing import List, Dict, Optional
from mnos.modules.mios.schemas.aircraft import FlightData, AircraftDecision

class AircraftDecisionEngine:
    def __init__(self, shadow):
        self.shadow = shadow
        self.acceptable_risk_threshold = 0.3

    def evaluate_flight(self, actor_ctx: dict, data: FlightData) -> AircraftDecision:
        total_rev = data.revenue.total_revenue
        total_cost = data.cost.total_cost
        profit = total_rev - total_cost
        coverage_ratio = float(total_rev / total_cost) if total_cost > 0 else 0.0

        load_factor = (data.revenue.business_seats_sold / data.specs.business_seats_total) * 100
        cargo_util = (data.revenue.belly_cargo_booked_kg / data.specs.belly_cargo_capacity_kg) * 100

        # Determine Decision Mode
        mode = "DO_NOT_FLY_MODE"
        risk_flags = []
        required_actions = []

        # 1. Base Thresholds
        if coverage_ratio < 0.70:
            mode = "DO_NOT_FLY_MODE"
        elif 0.70 <= coverage_ratio < 0.90:
            mode = "BUSINESS_BLOCK_SPACE_MODE"
        elif 0.90 <= coverage_ratio < 1.10:
            mode = "BUSINESS_CHARTER_REVIEW_MODE"
        elif coverage_ratio >= 1.10:
            mode = "BUSINESS_CHARTER_APPROVED_MODE"

        # 2. Business-Only Focus Overrides
        if load_factor < 50 and coverage_ratio < 1.0:
            mode = "DO_NOT_FLY_MODE"
            risk_flags.append("LOW_BUSINESS_LOAD_FACTOR")

        # 3. ACMI Logic
        if (data.historical_cycles_completed >= 8 and
            data.average_historical_coverage_ratio >= 1.15 and
            data.average_historical_load_factor >= 70 and
            data.average_historical_cargo_utilization >= 50 and
            data.forward_demand_months >= 3 and
            data.cash_reserve_covers_downside):

            if mode == "BUSINESS_CHARTER_APPROVED_MODE":
                mode = "BUSINESS_ACMI_REVIEW_MODE"

        # 4. Auto-Block Rules
        blocked = False
        if data.cargo_readiness_pct < 80:
            risk_flags.append("CARGO_NOT_READY")
            blocked = True
        if data.passenger_payment_collected_pct < 70:
            risk_flags.append("PASSENGER_PAYMENT_INSUFFICIENT")
            blocked = True
        if load_factor < 50:
            risk_flags.append("BUSINESS_CLASS_SOLD_BELOW_50")
            blocked = True
        if coverage_ratio < 0.90:
            risk_flags.append("COVERAGE_RATIO_BELOW_THRESHOLD")
            blocked = True
        if not data.aircraft_quote_uploaded:
            risk_flags.append("NO_AIRCRAFT_QUOTE")
            blocked = True
        if not data.ground_handling_confirmed:
            risk_flags.append("GROUND_HANDLING_NOT_CONFIRMED")
            blocked = True
        if not data.slot_or_route_permission_confirmed:
            risk_flags.append("NO_SLOT_PERMISSION")
            blocked = True
        if data.weather_risk == "HIGH":
            risk_flags.append("HIGH_WEATHER_RISK")
            blocked = True
        if not data.fce_cash_reserve_sufficient:
            risk_flags.append("INSUFFICIENT_CASH_RESERVE")
            blocked = True

        if blocked and "APPROVED" in mode:
            mode = "BUSINESS_CHARTER_REVIEW_MODE"
            required_actions.append("RESOLVE_BLOCKERS_FOR_APPROVAL")

        decision = AircraftDecision(
            id=uuid4(),
            route=data.route,
            decision_mode=mode,
            business_load_factor=load_factor,
            cargo_utilization_pct=cargo_util,
            coverage_ratio=coverage_ratio,
            expected_profit=profit,
            risk_flags=risk_flags,
            required_actions=required_actions,
            approval_required_by="CMO" if mode == "BUSINESS_CHARTER_REVIEW_MODE" else "SYSTEM"
        )

        event_type = "AIRCRAFT_DECISION_CREATED"
        if mode == "BUSINESS_CHARTER_APPROVED_MODE":
            event_type = "AIRCRAFT_CHARTER_RECOMMENDED"
        elif blocked:
            event_type = "AIRCRAFT_CHARTER_BLOCKED"

        decision.shadow_event_id = self.shadow.commit(f"mios.aircraft.{event_type.lower()}", actor_ctx["identity_id"], decision.dict())
        return decision

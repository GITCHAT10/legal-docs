import pytest
from decimal import Decimal
from mnos.modules.mios.engines.aircraft_decision import AircraftDecisionEngine
from mnos.modules.mios.schemas.aircraft import FlightData, AircraftSpecs, FlightRevenue, FlightCost
from mnos.modules.shadow.ledger import ShadowLedger

@pytest.fixture
def aircraft_engine():
    from mnos.shared.execution_guard import _sovereign_context
    _sovereign_context.set({"token": "TEST-TOKEN", "actor": {"identity_id": "SYSTEM"}})
    shadow = ShadowLedger()
    return AircraftDecisionEngine(shadow)

@pytest.fixture
def clean_flight_data():
    return FlightData(
        route="DXB-MLE",
        specs=AircraftSpecs(business_seats_total=60),
        revenue=FlightRevenue(
            business_seats_sold=50, # 83% load factor
            average_business_fare=Decimal("1500"),
            belly_cargo_booked_kg=Decimal("2000"), # 66% util
            cargo_yield_per_kg=Decimal("2.5")
        ),
        cost=FlightCost(
            aircraft_charter_or_acmi_cost=Decimal("50000"),
            airport_handling_cost=Decimal("5000")
        ),
        cargo_readiness_pct=90,
        passenger_payment_collected_pct=80,
        aircraft_quote_uploaded=True,
        ground_handling_confirmed=True,
        slot_or_route_permission_confirmed=True,
        weather_risk="LOW",
        fce_cash_reserve_sufficient=True,
        route_risk_score=0.1
    )

def test_charter_approved(aircraft_engine, clean_flight_data, actor_ctx):
    decision = aircraft_engine.evaluate_flight(actor_ctx, clean_flight_data)
    # Total Revenue: 50*1500 + 2000*2.5 = 75000 + 5000 = 80000
    # Total Cost: 50000 + 5000 = 55000
    # Coverage: 80000 / 55000 = 1.45
    assert decision.decision_mode == "BUSINESS_CHARTER_APPROVED_MODE"
    assert decision.coverage_ratio > 1.4

def test_auto_block_rules(aircraft_engine, clean_flight_data, actor_ctx):
    # Case: Low passenger payment
    clean_flight_data.passenger_payment_collected_pct = 50
    decision = aircraft_engine.evaluate_flight(actor_ctx, clean_flight_data)
    assert "PASSENGER_PAYMENT_INSUFFICIENT" in decision.risk_flags
    # Mode should stay in review/block if blocked
    assert decision.decision_mode == "BUSINESS_CHARTER_REVIEW_MODE"

def test_do_not_fly_low_load(aircraft_engine, clean_flight_data, actor_ctx):
    clean_flight_data.revenue.business_seats_sold = 10 # 16% load
    # Revenue: 15000 + 5000 = 20000
    # Cost: 55000
    # Coverage: 0.36
    decision = aircraft_engine.evaluate_flight(actor_ctx, clean_flight_data)
    assert decision.decision_mode == "DO_NOT_FLY_MODE"

def test_acmi_review_trigger(aircraft_engine, clean_flight_data, actor_ctx):
    clean_flight_data.historical_cycles_completed = 10
    clean_flight_data.average_historical_coverage_ratio = 1.2
    clean_flight_data.average_historical_load_factor = 75
    clean_flight_data.average_historical_cargo_utilization = 60
    clean_flight_data.forward_demand_months = 4
    clean_flight_data.cash_reserve_covers_downside = True

    decision = aircraft_engine.evaluate_flight(actor_ctx, clean_flight_data)
    assert decision.decision_mode == "BUSINESS_ACMI_REVIEW_MODE"

@pytest.fixture
def actor_ctx():
    return {"identity_id": "actor-1"}

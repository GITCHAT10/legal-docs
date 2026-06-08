import pytest
from mnos.modules.prestige.flight_matrix.transfer_feasibility_matrix import TransferFeasibilityMatrix
from mnos.modules.prestige.flight_matrix.recovery_workflow import RecoveryWorkflow
from mnos.modules.prestige.flight_matrix.models import FlightMatrixDecision

class MockShadow:
    def __init__(self):
        self.commits = []
    def commit(self, event_type, actor_id, payload):
        self.commits.append({"type": event_type, "actor": actor_id, "payload": payload})

class MockGuard:
    def is_authorized(self): return True
    def get_actor(self): return {"identity_id": "TEST_ACTOR"}

class MockCore:
    def __init__(self):
        self.shadow = MockShadow()
        self.guard = MockGuard()

@pytest.fixture
def core():
    return MockCore()

@pytest.fixture
def config():
    return {
        "seaplane_cutoff_time": "15:30",
        "international_to_seaplane_buffer_minutes": 60,
        "night_speedboat_review_after": "18:00",
        "night_speedboat_swell_red_threshold_m": 2.5,
        "heavy_baggage_markets": ["CIS", "GCC", "Global UHNW"]
    }

@pytest.fixture
def matrix(core, config):
    return TransferFeasibilityMatrix(core, None, config)

def test_seaplane_after_cutoff_returns_red(matrix):
    ctx = {
        "flight_number": "EK652",
        "resort_id": "RES-001",
        "transfer_mode": "SEAPLANE",
        "scheduled_arrival_time_mle": "15:00", # 15:00 + 60min = 16:00 > 15:30
    }
    decision = matrix.evaluate_feasibility({}, ctx)
    assert decision.feasibility_status == "RED"
    assert "SEAPLANE_CUTOFF_RISK" in decision.risk_reason_codes

def test_night_speedboat_outside_male_returns_yellow(matrix):
    ctx = {
        "flight_number": "SQ438",
        "resort_id": "RES-002",
        "transfer_mode": "SPEEDBOAT",
        "atoll_zone": "RAA", # Outside Male
        "scheduled_arrival_time_mle": "19:00",
    }
    decision = matrix.evaluate_feasibility({}, ctx)
    assert decision.feasibility_status == "YELLOW"
    assert "NIGHT_SPEEDBOAT_REVIEW_REQUIRED" in decision.risk_reason_codes

def test_night_speedboat_high_swell_returns_red(matrix):
    ctx = {
        "flight_number": "SQ438",
        "resort_id": "RES-002",
        "transfer_mode": "SPEEDBOAT",
        "atoll_zone": "KAAFU_NORTH",
        "scheduled_arrival_time_mle": "19:00",
        "swell_height_m": 3.0 # High swell
    }
    decision = matrix.evaluate_feasibility({}, ctx)
    assert decision.feasibility_status == "RED"
    assert "UNSAFE_NIGHT_SPEEDBOAT" in decision.risk_reason_codes

def test_baggage_risk_returns_yellow(matrix):
    ctx = {
        "flight_number": "SU320",
        "market_region": "CIS",
        "aircraft_capacity": "SMALL",
        "resort_id": "RES-001",
        "transfer_mode": "SPEEDBOAT",
        "scheduled_arrival_time_mle": "10:00"
    }
    decision = matrix.evaluate_feasibility({}, ctx)
    assert decision.feasibility_status == "YELLOW"
    assert "BAGGAGE_OFFLOAD_RISK" in decision.risk_reason_codes

def test_recovery_workflow_selection(core):
    workflow = RecoveryWorkflow(core)
    decision = FlightMatrixDecision(
        trace_id="TR-123",
        feasibility_status="RED",
        risk_reason_codes=["SEAPLANE_CUTOFF_RISK"],
        guest_segment="STANDARD"
    )
    result = workflow.initiate_recovery({"identity_id": "ADMIN"}, decision)
    assert result.selected_template == "LATE_SEAPLANE_RECOVERY"
    assert "daylight island arrival" in result.revised_proposal["guest_brief"].lower()

def test_p4_recovery_requires_human_approval(core):
    workflow = RecoveryWorkflow(core)
    decision = FlightMatrixDecision(
        trace_id="TR-P4",
        feasibility_status="RED",
        risk_reason_codes=["UNSAFE_NIGHT_SPEEDBOAT"],
        guest_segment="UHNW",
        human_approval_required=True
    )
    result = workflow.initiate_recovery({"identity_id": "ADMIN"}, decision)
    assert "HumanReview" in result.approvals_pending

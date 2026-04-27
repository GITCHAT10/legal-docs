import pytest
from ..ai.cognition import CognitiveBrain
from ..ai.predictions import PredictionEngine
from ..shadow_audit.ledger import ShadowLedger

@pytest.fixture
def ai_stack():
    ledger = ShadowLedger()
    brain = CognitiveBrain(ledger)
    ml = PredictionEngine(ledger)
    return {"brain": brain, "ml": ml, "ledger": ledger}

def test_ai_problem_solving(ai_stack):
    actor = {"identity_id": "u1", "device_id": "d1"}
    trace_id = "ai-trace-101"

    solution = ai_stack["brain"].solve_problem(actor, "resource_conflict", {"room": "101"}, trace_id)

    assert "strategy" in solution
    assert solution["confidence"] > 0.9

    # Verify audit
    assert ai_stack["ledger"].ledger[-1]["data"]["event_type"] == "ai.cognition.solution_generated"
    assert ai_stack["ledger"].ledger[-1]["data"]["trace_id"] == trace_id

def test_ml_workload_prediction(ai_stack):
    actor = {"identity_id": "u1", "device_id": "d1"}
    dataset = [10.0, 12.0, 15.0, 14.0]
    trace_id = "ml-trace-202"

    prediction = ai_stack["ml"].predict_workload(actor, dataset, trace_id)

    assert prediction["prediction"] > sum(dataset)/len(dataset)
    assert prediction["status"] == "VALIDATED"

    # Verify audit
    assert ai_stack["ledger"].ledger[-1]["data"]["event_type"] == "ml.prediction.generated"

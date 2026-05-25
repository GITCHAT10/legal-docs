import pytest
from fastapi.testclient import TestClient
from main import app, guard, shadow_core, ml_engine, ai_engine

client = TestClient(app)

@pytest.fixture
def auth_headers():
    return {
        "X-AEGIS-IDENTITY": "SYSTEM",
        "X-AEGIS-DEVICE": "SYS-01",
        "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_SYSTEM",
        "X-ISLAND-ID": "GLOBAL"
    }

def test_ai_intent_auditing(auth_headers):
    from main import identity_gateway
    identity_gateway.sessions["MOCK-AI-SESSION"] = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}

    payload = {"sender": "user1", "content": "I want to place an order for supplies"}
    response = client.post("/exmail/ingest?channel=whatsapp", json=payload, headers={"X-AEGIS-SESSION": "MOCK-AI-SESSION"})

    assert response.status_code == 200

    events = [b["event_type"] for b in shadow_core.chain]
    assert "ai.intent_analysis" in events

def test_ml_learning_from_ledger(auth_headers):
    from main import identity_gateway
    identity_gateway.sessions["MOCK-ML-SESSION"] = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}

    # 1. Manually add events to ledger
    with guard.sovereign_context({"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}):
        for i in range(5):
            shadow_core.commit("execution.confirmed", "TEST-ACTOR", {"order": i})

        # 2. Trigger training (Now inside context)
        ml_engine.train_from_ledger("delivery_efficiency", "execution.confirmed")

    # 3. Model should have updated strength
    prediction = ml_engine.predict_outcome("delivery_efficiency", {"type": "LOGISTICS"})
    assert prediction["confidence"] > 0.0

    # Verify ML update audit
    events = [b["event_type"] for b in shadow_core.chain]
    assert "ml.model_updated" in events

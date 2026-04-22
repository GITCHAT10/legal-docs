import pytest
from decimal import Decimal
from mnos.modules.fce.service import fce, FinancialException
from mnos.modules.shadow.service import shadow
from mnos.core.events.service import events
from mnos.core.ai.silvia import silvia
from mnos.interfaces.sky_i.comms.whatsapp import whatsapp
from mnos.modules.knowledge.service import knowledge_core
from mnos.shared.execution_guard import guard, in_sovereign_context

@pytest.fixture(autouse=True)
def setup_dna():
    knowledge_core.ingest("TEST", "Bookings and Arrivals and Emergencies active.")

def test_fail_closed_fce():
    with pytest.raises(FinancialException):
        fce.validate_pre_auth("FAIL", Decimal("1000"), Decimal("10"))

def test_shadow_fail_closed_on_context_violation():
    # Attempting to commit outside guard should raise RuntimeError
    with pytest.raises(RuntimeError, match="SOVEREIGN VIOLATION"):
        shadow.commit("ILLEGAL", {"data": "bad"})

def test_shadow_integrity_verification():
    shadow.chain = []
    shadow._seed_ledger()

    # Valid commit via guard
    ctx = {"device_id": "nexus-001", "bound_device_id": "nexus-001"}
    ctx["signature"] = aegis_sign(ctx)

    def logic(p): return "ok"
    guard.execute_sovereign_action("nexus.booking.created", {}, ctx, logic)

    assert shadow.verify_integrity() is True

    # Tamper
    shadow.chain[1]["event_type"] = "TAMPERED"
    assert shadow.verify_integrity() is False

def test_silvia_thresholds():
    res = silvia.process_request("Unknown command")
    assert res["status"] == "ESCALATE"

def test_workflow_concurrency_consistency():
    shadow.chain = []
    shadow._seed_ledger()
    ctx = {"device_id": "nexus-001", "bound_device_id": "nexus-001"}
    ctx["signature"] = aegis_sign(ctx)

    whatsapp.receive_message("+9601", "Book room", ctx)
    whatsapp.receive_message("+9602", "Arrival at airport", ctx)

    assert len(shadow.chain) >= 3
    assert shadow.verify_integrity() is True

def aegis_sign(payload):
    from mnos.core.security.aegis import aegis
    return aegis.sign_session(payload)

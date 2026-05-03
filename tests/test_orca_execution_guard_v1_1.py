import pytest
from mnos.core.orca.execution_guard import OrcaExecutionGuard
from mnos.core.aegis.session_guard import AegisSessionGuard
from mnos.modules.shadow.ledger import ShadowLedger

@pytest.fixture
def orca():
    sg = AegisSessionGuard()
    sl = ShadowLedger()
    return OrcaExecutionGuard(sg, sl)

def test_orca_execution_success(orca):
    actor = {"role": "ADMIN", "device_id": "D1"}
    event = {
        "event_type": "CORE.ACTION",
        "proof": {},
        "timestamp": "2025-01-01T00:00:00Z"
    }
    def task(): return "DONE"

    assert orca.execute(actor, event, task) == "DONE"
    assert len(orca.shadow_ledger.chain) == 1

def test_orca_dispatch_requires_proof(orca):
    actor = {"role": "ADMIN", "device_id": "D1"}
    event = {
        "event_type": "UT.DISPATCH.START",
        "proof": {},
        "timestamp": "2025-01-01T00:00:00Z"
    }
    def task(): return "DONE"

    with pytest.raises(PermissionError, match="ORCA REJECTION"):
        orca.execute(actor, event, task)

def test_orca_aegis_rejection(orca):
    actor = {"role": "GUEST"}
    event = {
        "event_type": "FCE.SETTLE",
        "proof": {},
        "timestamp": "2025-01-01T00:00:00Z"
    }
    with pytest.raises(PermissionError, match="AEGIS REJECTION"):
        orca.execute(actor, event, lambda: "OK")

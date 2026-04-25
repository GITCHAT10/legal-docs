import pytest
from mnos.core.nexus_init import NexusInit
from mnos.modules.ndt_se.engine import NdtSimEngine
from mnos.modules.shadow.ledger import ShadowLedger

def test_full_stack_handshake():
    init = NexusInit()
    result = init.execute_handshake("MIG-MARSGLOS-PROD-SECURE-INIT-2026")
    assert result["status"] == "READY_FOR_MERGE"

def test_shadow_ledger_integrity():
    ledger = ShadowLedger()
    h1 = ledger.commit("TEST_EVENT", "ACTOR_1", {"data": "A"})
    h2 = ledger.commit("TEST_EVENT", "ACTOR_2", {"data": "B"})
    assert h1 != h2
    assert ledger.chain[1]["prev_hash"] == h1

def test_ndt_integration():
    engine = NdtSimEngine()
    result = engine.run_national_simulation()
    assert result["status"] == "SIMULATION_COMPLETE"

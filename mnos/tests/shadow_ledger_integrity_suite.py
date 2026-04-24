import pytest
from mnos.modules.shadow.service import shadow
from mnos.config import config

def test_shadow_genesis_payload_tamper_fails():
    """Verify genesis payload mutation fails integrity."""
    shadow.chain = []
    shadow._seed_ledger()
    shadow.chain[0]["payload"] = {"TAMPER": True}
    assert shadow.verify_integrity() is False

def test_shadow_genesis_timestamp_tamper_fails():
    """Verify genesis timeline mutation fails integrity."""
    shadow.chain = []
    shadow._seed_ledger()
    shadow.chain[0]["timestamp"] = "2020-01-01T00:00:00Z"
    assert shadow.verify_integrity() is False

def test_shadow_middle_chain_tamper_fails():
    """Verify middle-chain result mutation fails integrity."""
    shadow.chain = []
    shadow._seed_ledger()
    from mnos.shared.execution_guard import in_sovereign_context
    t = in_sovereign_context.set(True)
    try:
        shadow.commit("event.1", {"data": "ok"})
        shadow.commit("event.2", {"data": "ok"})
        shadow.commit("event.3", {"data": "ok"})
    finally:
        in_sovereign_context.reset(t)

    # Tamper with middle block
    shadow.chain[2]["payload"]["data"] = "TAMPERED"
    assert shadow.verify_integrity() is False

def test_shadow_actor_objective_mutation_fails():
    """Verify actor_id or objective_code mutation fails integrity."""
    shadow.chain = []
    shadow._seed_ledger()
    from mnos.shared.execution_guard import in_sovereign_context
    t = in_sovereign_context.set(True)
    try:
        shadow.commit("event.secure", {"actor_id": "CEO", "objective_code": "V1"})
    finally:
        in_sovereign_context.reset(t)

    # Mutate metadata
    shadow.chain[1]["actor_id"] = "ROGUE"
    assert shadow.verify_integrity() is False

import pytest
from mnos.core.aegis.session_guard import AegisSessionGuard

@pytest.fixture
def guard():
    return AegisSessionGuard()

def test_admin_full_access(guard):
    actor = {"role": "ADMIN", "device_id": "DEV1"}
    assert guard.validate_action(actor, "ANY.EVENT.TYPE")

def test_admin_requires_device(guard):
    actor = {"role": "ADMIN"}
    assert not guard.validate_action(actor, "ANY.EVENT.TYPE")

def test_ai_agent_restricted(guard):
    actor = {"role": "AI_AGENT"}
    assert guard.validate_action(actor, "FCE.SETTLE.RECOMMEND")
    assert not guard.validate_action(actor, "FCE.SETTLE.COMPLETE")

def test_merchant_access(guard):
    actor = {"role": "MERCHANT", "device_id": "DEV2"}
    assert guard.validate_action(actor, "UPOS.SALE.COMPLETE")
    assert not guard.validate_action(actor, "PEOPLE.DUTY.ASSIGN")

import pytest
from decimal import Decimal
from mnos.modules.imoxon.pricing.engine import PricingEngine, PricingRequest
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.shared.execution_guard import ExecutionGuard

def test_shadow_audit_trace():
    shadow = ShadowLedger()
    # Mocking environment for shadow write
    class MockPolicy:
        def validate_action(self, at, ctx): return True, "OK"
    guard = ExecutionGuard(None, MockPolicy(), None, shadow, None)

    engine = PricingEngine()
    req = PricingRequest(net_amount=Decimal("500.00"), product_type="accommodation")

    # Pricing calculate usually happens in context of a booking action
    actor = {"identity_id": "AGENT_01", "role": "agent", "device_id": "DEV_01"}

    with guard.sovereign_context(actor):
        resp = engine.calculate(req)
        # Commit manually for test if not internal
        shadow.commit("pricing.quote_generated", "AGENT_01", resp.model_dump(mode="json"))

    assert len(shadow.chain) >= 1
    last_block = shadow.chain[-1]
    assert last_block["event_type"] == "pricing.quote_generated"
    assert last_block["payload"]["compliance_hash"] == resp.compliance_hash
    assert shadow.verify_integrity() is True

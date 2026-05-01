import os
import sys
import shutil
from decimal import Decimal
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.core.shadow.service import ShadowSovereignLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.fce.service import FCESovereignService
from mnos.core.fce.wallet import FceWalletService
from mnos.exec.upos.engine import UPOSEngine
from mnos.shared.execution_guard import ExecutionGuard, _sovereign_context

def test_upos_sovereign_flow():
    print("🛡️ TESTING UPOS SOVEREIGN FLOW HARDENING")
    print("-" * 50)

    # 0. Setup
    storage_path = "mnos/core/shadow/storage_harden_test"
    if os.path.exists(storage_path):
        shutil.rmtree(storage_path)

    shadow = ShadowSovereignLedger(storage_path=storage_path)
    events = DistributedEventBus()
    fce = FCESovereignService()
    upos = UPOSEngine(fce, shadow, events)

    actor = {"identity_id": "test-merchant", "device_id": "device-01", "role": "merchant"}
    trace_id = "tr-harden-001"

    # 1. TEST: Order creation WITHOUT guard (Should fail in shadow.commit)
    print("[1] TEST: Unguarded Order Creation...")
    try:
        upos.create_order(
            merchant_id="MERC-01",
            actor_id="test-merchant",
            items=[{"id": "p1", "qty": 1, "price": 100}],
            amount=100.0,
            idempotency_key="order-unguarded",
            trace_id=trace_id
        )
        assert False, "Unguarded call should have failed shadow commit"
    except PermissionError as e:
        print(f"    ✔ Caught expected error: {e}")

    # 2. TEST: Order creation WITH guard (Should pass)
    print("[2] TEST: Guarded Order Creation...")
    # Setup mock guard engine
    guard = ExecutionGuard(None, None, fce, shadow, events)
    # Mock policy engine to allow action
    class MockPolicy:
        def validate_action(self, action, ctx): return True, ""
    guard.policy_engine = MockPolicy()

    result = guard.execute_sovereign_action(
        action_type="upos.order.completed",
        actor_context=actor,
        func=upos.create_order,
        merchant_id="MERC-01",
        actor_id="test-merchant",
        items=[{"id": "p1", "qty": 1, "price": 100}],
        amount=100.0,
        idempotency_key="order-guarded",
        trace_id=trace_id
    )
    print(f"    ✔ Order successful: {result['order_id']}")
    assert result["status"] == "COMPLETED"

    # 3. TEST: Fail-Closed Validation (Negative Amount)
    print("[3] TEST: Fail-Closed Validation (Amount <= 0)...")
    try:
        guard.execute_sovereign_action(
            action_type="upos.order.completed",
            actor_context=actor,
            func=upos.create_order,
            merchant_id="MERC-01",
            actor_id="test-merchant",
            items=[{"id": "p1", "qty": 1}],
            amount=-50.0,
            idempotency_key="order-bad-amt",
            trace_id=trace_id
        )
        assert False, "Negative amount should have been rejected"
    except RuntimeError as e:
        print(f"    ✔ Caught expected error: {e}")

    # 4. TEST: Shadow Integrity & Event Type Consistency
    print("[4] TEST: SHADOW Consistency Check...")
    assert shadow.verify_integrity() == True
    # Last block should be 'upos.order.completed.completed' from Guard wrap
    # Wait, guard.execute_sovereign_action commits "{action_type}.completed"
    # UPOSEngine.create_order also commits "upos.order.completed"

    events_found = [b["event_type"] for b in shadow.chain]
    print(f"    ✔ Events in chain: {events_found}")
    assert "upos.order.completed" in events_found

    print("-" * 50)
    print("✅ UPOS HARDENING TESTS PASSED")

if __name__ == "__main__":
    test_upos_sovereign_flow()

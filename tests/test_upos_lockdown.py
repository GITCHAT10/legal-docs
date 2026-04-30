import os
import sys
import shutil
import uuid
from decimal import Decimal
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.core.shadow.service import ShadowSovereignLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.fce.service import FCESovereignService
from mnos.exec.upos.engine import UPOSEngine
from mnos.shared.execution_guard import ExecutionGuard
from mnos.interfaces.orca.dashboard import OrcaDashboard

def test_upos_lockdown():
    print("🔒 TESTING UPOS SALA NODE LOCKDOWN")
    print("-" * 50)

    # 0. Setup
    storage_path = "mnos/core/shadow/storage_lockdown_test"
    if os.path.exists(storage_path):
        shutil.rmtree(storage_path)

    shadow = ShadowSovereignLedger(storage_path=storage_path)
    events = DistributedEventBus()
    fce = FCESovereignService()
    upos = UPOSEngine(fce, shadow, events)
    dashboard = OrcaDashboard(shadow, None) # Wallet not needed for revenue

    actor = {"identity_id": "test-staff", "device_id": "TAB-001", "role": "staff", "verified": True}
    trace_id = "tr-lockdown-001"

    # 1. TEST: ExecutionGuard Mandatory (Should fail in engine setup)
    print("[1] TEST: No ExecutionGuard -> No Order...")
    try:
        upos.create_order(
            merchant_id="M1",
            actor_id="test-staff",
            items=[{"id": "p1", "qty": 1}],
            amount=100.0,
            idempotency_key="k1",
            trace_id=trace_id
        )
        assert False, "Should have failed shadow.commit authorization check"
    except PermissionError as e:
        print(f"    ✔ Blocked unguarded access: {e}")

    # 2. TEST: Valid Sovereign Flow (5 stages)
    print("[2] TEST: Standardized Lifecycle (requested -> completed)...")
    guard = ExecutionGuard(None, None, fce, shadow, events)
    class MockPolicy:
        def validate_action(self, action, ctx): return True, ""
    guard.policy_engine = MockPolicy()

    order = guard.execute_sovereign_action(
        action_type="upos.order",
        actor_context=actor,
        func=upos.create_order,
        merchant_id="M1",
        actor_id="test-staff",
        items=[{"id": "p1", "qty": 1}],
        amount=100.0,
        idempotency_key="k2",
        trace_id=trace_id
    )
    print(f"    ✔ Order completed: {order['order_id']}")
    assert order["status"] == "COMPLETED"

    # Check shadow chain for all 5 stages + guard stages
    stages = [b["event_type"] for b in shadow.chain if "upos.order" in b["event_type"]]
    print(f"    ✔ Audit stages found: {stages}")
    assert "upos.order.requested" in stages
    assert "upos.order.validated" in stages
    assert "upos.order.approved" in stages
    assert "upos.order.executed" in stages
    assert "upos.order.completed" in stages

    # 3. TEST: Dashboard Revenue Recognition
    print("[3] TEST: Revenue recognition only for completed orders...")
    # Count how many completed orders so far
    initial_completed_count = len([b for b in shadow.chain if b["event_type"] == "upos.order.completed"])

    # Manual commit of 'requested' only to see if it counts
    # We need authorized context for manual shadow commit
    with ExecutionGuard.authorized_context(actor):
        shadow.commit("upos.order.requested", "staff", {"amount": 500, "pricing": {"total": 500}}, trace_id="tr-3")

    metrics = dashboard.get_live_metrics()
    print(f"    ✔ Total Revenue: {metrics['total_revenue_mvr']} MVR")
    # Should reflect only the completed orders
    # From step 2, there was 1 completed order (total 128.7)
    assert metrics["order_count"] == initial_completed_count

    # 4. TEST: Dashboard Offline Resilience (Missing Pricing)
    print("[4] TEST: Dashboard Offline resilience (No pricing)...")
    with ExecutionGuard.authorized_context(actor):
        shadow.commit("upos.order.completed", "staff", {"amount": 200}, trace_id="tr-4")

    metrics = dashboard.get_live_metrics()
    print(f"    ✔ Metrics with offline order: {metrics['total_revenue_mvr']} MVR")
    # Fallback to amount 200 should work
    assert metrics["total_revenue_mvr"] == 128.7 + 200.0
    print("    ✔ Dashboard stable without pricing payload.")

    # 5. TEST: FCE Validation Failure blocks UPOS
    print("[5] TEST: FCE failure blocks completion...")
    try:
        guard.execute_sovereign_action(
            action_type="upos.order",
            actor_context=actor,
            func=upos.create_order,
            merchant_id="M1",
            actor_id="test-staff",
            items=[{"id": "p1", "qty": 1}],
            amount=-1.0, # Will fail FCE
            idempotency_key="k3",
            trace_id=trace_id
        )
    except RuntimeError:
        print("    ✔ Caught expected FCE failure.")

    # 6. TEST: .env loading simulation
    print("[6] TEST: .env loading simulation...")
    with open(".env.test", "w") as f:
        f.write("# comment\nKEY=VAL\n\n# another\nFOO=BAR")

    # Simple python equivalent of the bash set -a; source
    env_vars = {}
    with open(".env.test", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env_vars[k] = v
    assert env_vars["KEY"] == "VAL"
    assert env_vars["FOO"] == "BAR"
    print("    ✔ Env loader handled comments/blank lines.")

    print("-" * 50)
    print("✅ UPOS LOCKDOWN TESTS PASSED")

if __name__ == "__main__":
    test_upos_lockdown()

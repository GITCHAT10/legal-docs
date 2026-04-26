from mnos.shared.guard.test_signer import aegis_sign
import pytest
from decimal import Decimal
from mnos.modules.fce.service import fce
from mnos.modules.shadow.service import shadow
from mnos.modules.shadow_sync.service import shadow_sync
from mnos.core.security.aegis import aegis, SecurityException
from mnos.shared.execution_guard import guard
from mnos.core.events.service import events


from mnos.core.apollo.registry import apollo_registry

def test_aegis_spoof_attack():
    """Verify spoofing fails (server-side hardware binding only)."""
    import time
    # Hardware not in registry
    ctx = {
        "user_id": "ATTACKER",
        "session_id": "S-ROGUE",
        "device_id": "nexus-SPOOFED-ID",
        "issued_at": int(time.time()),
        "nonce": "N-BAD"
    }
    ctx["signature"] = aegis_sign(ctx)
    with pytest.raises(SecurityException, match="(failed cryptographic verification|SYSTEM HALT)"):
        guard.execute_sovereign_action("test", {}, ctx, lambda x: "fail")

def test_shadow_genesis_tamper_fail_closed():
    """Verify fail-closed on genesis block tampering."""
    shadow.chain = []
    shadow._seed_ledger()
    # Direct memory tampering
    shadow.chain[0]["hash"] = "CORRUPTED"
    with pytest.raises(RuntimeError, match="Chain corruption detected"):
        from mnos.shared.execution_guard import in_sovereign_context
        t = in_sovereign_context.set(True)
        try:
            shadow.commit("fail_test", {})
        finally:
            in_sovereign_context.reset(t)

@pytest.fixture(autouse=True)
def reset_system():
    # Reset Registry State
    apollo_registry._system_locked = False
    apollo_registry._used_nonces = set()
    shadow.chain = []
    shadow._seed_ledger()

def test_shadow_sync_disconnection_lifecycle():
    """Simulate CABLE_CUT -> Local Execution -> Reconnect -> Reconcile."""
    import time
    # 1. Cloud mode (default)
    assert shadow_sync.mode == "READ_ONLY"

    # 2. Trigger CABLE_CUT via Guard (Authorized trigger)
    ctx = {
        "user_id": "CEO-01",
        "session_id": "S-01",
        "device_id": "nexus-admin-01",
        "issued_at": int(time.time()),
        "nonce": "N-SYNC"
    }
    ctx["signature"] = aegis_sign(ctx)
    guard.execute_sovereign_action(
        "nexus.emergency.triggered",
        {"type": "CABLE_CUT"},
        ctx,
        lambda x: "promoted"
    )
    assert shadow_sync.mode == "READ_WRITE"

    # 3. Perform local transactions
    local_data = {"booking_id": "LOCAL-101", "guest": "Mohamed"}
    shadow_sync.process_local_execution("nexus.booking.created", local_data)
    assert len(shadow_sync.local_queue) == 1

    # 4. Reconnect & Reconcile
    # Reconcile uses events.publish which also requires context
    from mnos.shared.execution_guard import in_sovereign_context
    t = in_sovereign_context.set(True)
    try:
        count = shadow_sync.reconcile_with_cloud()
    finally:
        in_sovereign_context.reset(t)

    assert count == 1
    assert shadow_sync.mode == "READ_ONLY"
    # Verify transaction reached SHADOW via events
    # Note: Booking workflow triggers payment event, so we check for booking.created in the chain
    event_types = [entry["event_type"] for entry in shadow.chain]
    assert "nexus.booking.created" in event_types

def test_mira_real_scenarios():
    """Validate 12h rule, child exemption, and TGST overrides."""
    # 12h rule
    res1 = fce.calculate_folio(Decimal("1000"), stay_hours=11.9)
    assert res1["green_tax"] == Decimal("0.00")

    # Child exemption
    res2 = fce.calculate_folio(Decimal("1000"), is_child=True)
    assert res2["green_tax"] == Decimal("0.00")

    # TGST switch
    res3 = fce.calculate_folio(Decimal("1000"), effective_tgst=Decimal("0.16"))
    assert res3["tgst_rate"] == Decimal("0.16")

def test_efaas_identity_mapping():
    """Verify eFaas identity payload mapping accuracy."""
    oidc = {
        "id_number": "A123456",
        "name": "Ahmed Ibrahim",
        "birthdate": "1992-04-20",
        "email_verified": True
    }
    mapping = aegis._map_efaas_identity(oidc)
    assert mapping["national_id"] == "A123456"
    assert mapping["full_name"] == "Ahmed Ibrahim"
    assert mapping["birthdate"] == "1992-04-20"

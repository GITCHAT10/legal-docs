import pytest
import time
from decimal import Decimal
from mnos.shared.guard.service import guard, ExecutionMode
from mnos.core.aig_aegis.service import aig_aegis
from mnos.modules.exmail.service import exmail_authority
from mnos.modules.aig_vault.service import aig_vault
from mnos.modules.aig_shadow.service import aig_shadow

@pytest.fixture
def admin_ctx():
    ts = int(time.time())
    ctx = {
        "device_id": "nexus-admin-01",
        "biometric_verified": True,
        "nonce": f"nonce-{time.time()}",
        "timestamp": ts,
        "mission_scope": "V1"
    }
    ctx["signature"] = aig_aegis.sign_session(ctx)
    return ctx

@pytest.fixture
def orban_conn():
    return {
        "is_vpn": True,
        "tunnel": "aig_tunnel",
        "encryption": "wireguard",
        "tunnel_id": "MIG-SALA-01",
        "source_ip": "10.0.0.1",
        "node_id": "SALA-EDGE-01"
    }

def test_exmail_success_with_context(admin_ctx, orban_conn):
    """ExMAIL inbound processing succeeds with valid connection_context."""
    res = exmail_authority.ingest_inbound_exmail(
        sender="test@mig.mv",
        subject="Booking",
        body="Ahmed room Dec 1",
        session_context=admin_ctx,
        request_data={"connection_context": orban_conn}
    )
    assert res["status"] == "SUCCESS"

def test_exmail_degraded_fallback(admin_ctx):
    """Operational non-critical actions can survive controlled degraded mode."""
    # Pass NO connection_context, ExMAIL should default it but we can force DEGRADED mode
    res = exmail_authority.ingest_inbound_exmail(
        sender="test@mig.mv",
        subject="Inquiry",
        body="Details please",
        session_context=admin_ctx,
        mode="DEGRADED"
    )
    assert res["status"] == "SUCCESS"

    # Verify SHADOW log for DEGRADED and sync_required
    latest = aig_shadow.chain[-1]
    assert latest["payload"]["data"]["mode"] == "DEGRADED"
    assert latest["payload"]["data"]["sync_required"] is True

def test_critical_blocked_in_degraded(admin_ctx, orban_conn):
    """CRITICAL actions cannot execute in DEGRADED mode."""
    def critical_logic(p): return "DONE"

    with pytest.raises(RuntimeError, match="prohibited in DEGRADED mode"):
        guard.execute_sovereign_action(
            "SYSTEM_SHUTDOWN",
            {},
            admin_ctx,
            critical_logic,
            connection_context=orban_conn,
            tenant="MIG-ADMIN",
            mode=ExecutionMode.DEGRADED,
            objective_code="J5" # Critical
        )

def test_vault_write_resolves_role(admin_ctx, orban_conn):
    """uCloud write works for nexus-admin-01 by resolving role."""
    # admin_ctx has device_id: nexus-admin-01
    # Aegis validate_session will add resolved_role: nexus-admin
    aig_aegis.validate_session(admin_ctx)

    # AIGVault check_permission uses resolved_role
    assert aig_vault.check_permission("nexus-admin", "write", admin_ctx) is True

def test_vault_rejects_guest_write(orban_conn):
    """uCloud write fails for nexus-guest-01."""
    ts = int(time.time())
    guest_ctx = {
        "device_id": "nexus-guest-01",
        "biometric_verified": True,
        "nonce": f"nonce-guest-{time.time()}",
        "timestamp": ts
    }
    guest_ctx["signature"] = aig_aegis.sign_session(guest_ctx)
    aig_aegis.validate_session(guest_ctx)

    with pytest.raises(Exception, match="denied 'write' access"):
        aig_vault.check_permission("nexus-guest", "write", guest_ctx)

def test_shadow_rollback_on_fail(admin_ctx, orban_conn):
    """Verify shadow intent is rolled back if execution logic fails."""
    initial_len = len(aig_shadow.chain)

    def failing_logic(p): raise ValueError("BOOM")

    with pytest.raises(ValueError, match="BOOM"):
        guard.execute_sovereign_action(
            "test.fail",
            {},
            admin_ctx,
            failing_logic,
            connection_context=orban_conn,
            tenant="MIG-TEST"
        )

    # Chain length should be same as initial (intent was popped)
    assert len(aig_shadow.chain) == initial_len

import pytest
from decimal import Decimal
from mnos.modules.fce.service import fce
from mnos.modules.shadow.service import shadow
from mnos.shared.execution_guard import guard
from mnos.core.security.aegis import aegis

def aegis_sign(payload):
    return aegis.sign_session(payload)

def test_tax_edge_case_zero_base():
    """Verify FCE handles zero base amount correctly."""
    res = fce.calculate_folio(Decimal("0.00"), pax=2, nights=3)
    # Service charge 10% of 0 = 0
    # TGST 17% of 0 = 0
    # Green tax $6 * 2 * 3 = $36
    assert res["total"] == Decimal("36.00")

def test_tax_edge_case_high_pax():
    """Verify FCE handles large pax and nights counts."""
    res = fce.calculate_folio(Decimal("1000.00"), pax=10, nights=10)
    # Base 1000
    # SC 100
    # Taxable 1100
    # TGST (1100 * 0.17) = 187
    # Green tax (6 * 10 * 10) = 600
    # Total: 1100 + 187 + 600 = 1887
    assert res["total"] == Decimal("1887.00")

def test_ledger_tamper_hard_fail():
    """Verify that tampering with any block prevents further commits."""
    shadow.chain = []
    shadow._seed_ledger()
    ctx = {"device_id": "nexus-admin-01", "biometric_verified": True}
    ctx["signature"] = aegis_sign(ctx)

    conn = {
        "is_vpn": True,
        "tunnel_id": "tun-01",
        "encryption": "wireguard",
        "tunnel": "orban",
        "source_ip": "10.0.0.1",
        "node_id": "ADMIN-01"
    }

    guard.execute_sovereign_action("nexus.booking.created", {}, ctx, lambda x: "ok", connection_context=conn)

    # Tamper with block 1 hash in head's previous_hash link
    # This simulates a direct DB mutation of a sealed link
    shadow.chain[1]["previous_hash"] = "CORRUPT"

    with pytest.raises(RuntimeError, match="Chain corruption detected"):
        guard.execute_sovereign_action("nexus.booking.created", {}, ctx, lambda x: "ok", connection_context=conn)

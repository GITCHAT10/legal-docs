import pytest
from decimal import Decimal
from mnos.modules.ut.service import ut_service
from mnos.core.aig_aegis.service import aig_aegis, SecurityException
from mnos.modules.fce.service import FinancialException

@pytest.fixture
def ut_session():
    # Valid dispatch session
    payload = {"device_id": "ut-dispatch-01", "biometric_verified": True}
    sig = aig_aegis.sign_session(payload)
    payload["signature"] = sig
    return payload

@pytest.fixture
def ut_connection():
    return {
        "is_vpn": True,
        "tunnel_id": "ut-tunnel-01",
        "encryption": "wireguard",
        "tunnel": "aig_tunnel",
        "source_ip": "10.0.0.10",
        "node_id": "UT-EDGE-01"
    }

def test_ut_booking_flow_success(ut_session, ut_connection):
    """Verify UT booking flow with cloud integration and NEXUS authority."""
    booking_data = {"customer_id": "C-001", "amount": "150.00", "limit": "500.00"}
    res = ut_service.create_booking(booking_data, ut_session, ut_connection)

    assert res["status"] == "BOOKED"
    assert "booking_id" in res
    assert res["amount_authorized"] == "150.00"

def test_ut_booking_fail_closed_finance(ut_session, ut_connection):
    """Verify UT booking fails if NEXUS finance authority (FCE) denies it."""
    booking_data = {"customer_id": "C-FAIL", "amount": "2000.00", "limit": "500.00"}

    with pytest.raises(FinancialException, match="FCE AUTH DENIED"):
        ut_service.create_booking(booking_data, ut_session, ut_connection)

def test_ut_dispatch_governance_success(ut_session, ut_connection):
    """Verify UT critical cargo dispatch requires L5 governance."""
    evidence = {"reason": "Authorized Shipment", "timestamp": "2026-04-22T15:00:00Z", "confirmed": True}
    approvals = ["ut-dispatch-01"]

    res = ut_service.dispatch_cargo("CARGO-99", ut_session, ut_connection, evidence, approvals)
    assert res["status"] == "DISPATCHED"

def test_ut_security_failure_untrusted_device(ut_connection):
    """Verify UT fails if an untrusted device attempts access."""
    bad_payload = {"device_id": "attacker-device", "biometric_verified": True}
    sig = aig_aegis.sign_session(bad_payload)
    bad_payload["signature"] = sig

    with pytest.raises(SecurityException, match="Unauthorized or inactive device"):
        ut_service.create_booking({}, bad_payload, ut_connection)

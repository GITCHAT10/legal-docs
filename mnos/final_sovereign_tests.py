import pytest
import uuid
from decimal import Decimal
from mnos.modules.fce.service import fce, FinancialException
from mnos.modules.aig_shadow.service import aig_shadow
from mnos.core.ai.silvia import silvia
from mnos.interface.mig_tactical_panel.sky_i.comms.whatsapp import whatsapp
import mnos.modules.workflows.booking
import mnos.modules.workflows.guest_arrival
from mnos.modules.knowledge.service import knowledge_core
from mnos.shared.guard.service import guard
from mnos.core.aig_aegis.service import aig_aegis

@pytest.fixture(autouse=True)
def reset_ledger():
    aig_shadow.chain = []
    aig_shadow._seed_ledger()
    knowledge_core.ingest("TEST_DNA", "Bookings and Arrivals and Emergencies active.")

def aig_aegis_sign(payload):
    return aig_aegis.sign_session(payload)

def test_fail_closed_fce():
    """Verify FCE blocks over-limit transactions."""
    with pytest.raises(FinancialException, match="FCE AUTH DENIED"):
        fce.validate_pre_auth("F-FAIL", Decimal("10000"), Decimal("100"))

def test_aig_shadow_genesis_integrity():
    """Verify that genesis block is valid and anchored."""
    assert aig_shadow.chain[0]["entry_id"] == 0
    assert aig_shadow.verify_integrity() is True

def test_silvia_intelligence_thresholds():
    """Verify SILVIA refuses borderline or unknown intent."""
    res = silvia.process_request("I want to order food")
    assert res["status"] == "ESCALATE"

def test_whatsapp_hardened_flow():
    """Verify end-to-end WhatsApp flow via Execution Guard with signed session."""
    ctx = {"device_id": "nexus-001", "biometric_verified": True}
    ctx["signature"] = aig_aegis_sign(ctx)

    conn = {"is_vpn": True, "tunnel_id": "tun-01", "encryption": "wireguard"}

    # Mock the receive_message to pass connection context if it were real,
    # but since whatsapp.py doesn't take it yet, we might need to update it or
    # update the guard to have defaults for legacy calls.
    # Actually, I'll update the test to pass it if I update whatsapp.py.
    # For now, let's update whatsapp.py to be aware of the new guard requirements.

    res = whatsapp.receive_message("+9601112222", "I want to book a room", ctx)
    # This will still fail until whatsapp.py is updated to pass connection_context
    assert res["status"] == "PROCESSED"
    assert "NEXUS booking" in res["response"]
    assert aig_shadow.verify_integrity() is True

def test_concurrent_integrity_sim():
    """Verify multiple workflows maintain immutable chain integrity."""
    ctx = {"device_id": "nexus-001", "biometric_verified": True}
    ctx["signature"] = aig_aegis_sign(ctx)

    # Sequence of events
    whatsapp.receive_message("+9601", "Book room", ctx)
    whatsapp.receive_message("+9602", "Arrival", ctx)

    # Analysis:
    # 1. Genesis (1)
    # 2. WhatsApp:Book -> Guard -> Logic -> Shadow (2)
    # 3. HandleBooking -> Events.Publish(Payment) -> Shadow (3)
    # 4. WhatsApp:Arrival -> Guard -> Logic -> Shadow (4)
    # Total: 4 entries
    assert len(aig_shadow.chain) >= 4
    assert aig_shadow.verify_integrity() is True

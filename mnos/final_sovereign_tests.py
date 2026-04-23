import pytest
import uuid
from decimal import Decimal
from mnos.modules.fce.service import fce, FinancialException
from mnos.modules.shadow.service import shadow
from mnos.core.asi.silvia import silvia
from mnos.interfaces.sky_i.comms.whatsapp import whatsapp
import mnos.modules.workflows.booking
import mnos.modules.workflows.guest_arrival
from mnos.modules.knowledge.service import knowledge_core
from mnos.shared.execution_guard import guard
from mnos.core.security.aegis import aegis

@pytest.fixture(autouse=True)
def reset_ledger():
    shadow.chain = []
    shadow._seed_ledger()
    knowledge_core.ingest("TEST_DNA", "Bookings and Arrivals and Emergencies active.")

def aegis_sign(payload):
    return aegis.sign_session(payload)

def test_fail_closed_fce():
    """Verify FCE blocks over-limit transactions."""
    with pytest.raises(FinancialException, match="FCE AUTH DENIED"):
        fce.validate_pre_auth("F-FAIL", Decimal("10000"), Decimal("100"))

def test_shadow_genesis_integrity():
    """Verify that genesis block is valid and anchored."""
    assert shadow.chain[0]["entry_id"] == 0
    assert shadow.verify_integrity() is True

def test_silvia_intelligence_thresholds():
    """Verify SILVIA refuses borderline or unknown intent."""
    res = silvia.process_request("I want to order food")
    assert res["status"] == "ESCALATE"

def test_whatsapp_hardened_flow():
    """Verify end-to-end WhatsApp flow via Execution Guard with signed session."""
    ctx = {
        "user_id": "GUEST-01",
        "session_id": "SESS-101",
        "device_id": "nexus-001",
        "issued_at": 1700000000,
        "nonce": "N-101"
    }
    ctx["signature"] = aegis_sign(ctx)

    res = whatsapp.receive_message("+9601112222", "I want to book a room", ctx)
    assert res["status"] == "PROCESSED"
    assert "NEXUS booking" in res["response"]
    assert shadow.verify_integrity() is True

def test_concurrent_integrity_sim():
    """Verify multiple workflows maintain immutable chain integrity."""
    # Use different phone numbers to avoid any caching side effects if they existed
    ctx = {
        "user_id": "GUEST-01",
        "session_id": "SESS-102",
        "device_id": "nexus-001",
        "issued_at": 1700000000,
        "nonce": "N-102"
    }
    ctx["signature"] = aegis_sign(ctx)

    # 1. Book Room (Triggers 2 entries: exmail/whatsapp received + payment received)
    whatsapp.receive_message("+9601001", "Book room", ctx.copy())

    # 2. Arrival (Triggers 1 entry)
    whatsapp.receive_message("+9601002", "Arrival", ctx.copy())

    # Chain:
    # [0] GENESIS
    # [1] nexus.booking.created (via whatsapp)
    # [2] nexus.payment.received (via handle_booking subscriber)
    # [3] nexus.guest.arrival (via whatsapp)

    assert len(shadow.chain) == 4
    assert shadow.verify_integrity() is True

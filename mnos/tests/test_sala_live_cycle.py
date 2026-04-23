import pytest
from decimal import Decimal
from mnos.modules.exmail.service import exmail_authority
from mnos.infrastructure.mig_event_spine.service import events
from mnos.modules.fce.service import fce
from mnos.core.aig_aegis.service import aig_aegis
from mnos.modules.aig_shadow.service import aig_shadow
from mnos.shared.guard.service import guard

# Initialize workflow for the test
from mnos.modules.workflows.reservation import reservation_workflow

import time

@pytest.fixture
def vvvip_session():
    payload = {
        "device_id": "nexus-admin-01",
        "biometric_verified": True,
        "mission_scope": "V1",
        "nonce": str(time.time()),
        "timestamp": int(time.time())
    }
    sig = aig_aegis.sign_session(payload)
    payload["signature"] = sig
    return payload

@pytest.fixture
def orban_context():
    return {
        "is_vpn": True,
        "tunnel_id": "MIG-SALA-01",
        "encryption": "wireguard",
        "tunnel": "aig_tunnel",
        "source_ip": "10.0.0.1",
        "node_id": "SALA-EDGE-01"
    }

def test_sala_live_cycle_e2e(vvvip_session, orban_context):
    """
    End-to-End Proof:
    ExMAIL Ingress -> Guest/Reservation Workflow -> FCE Finalization -> SHADOW Audit
    """
    # 1. ExMAIL Ingress (Inbound Booking)
    booking_body = "I would like to book a room for Ahmed. Dates: Dec 1-5."
    # Mocking silvia's extracted_data for the test context
    from mnos.core.ai.silvia import silvia
    original_process = silvia.process_request
    silvia.process_request = lambda text: {
        "intent": "booking.created",
        "response": "Processing your booking.",
        "extracted_data": {"guest_name": "Ahmed", "dates": "Dec 1-5"}
    }

    res_exmail = exmail_authority.ingest_inbound_exmail(
        sender="ahmed@example.mv",
        subject="Booking Request",
        body=booking_body,
        session_context=vvvip_session,
        request_data={"connection_context": orban_context}
    )
    assert res_exmail["status"] == "SUCCESS"

    # Restore silvia
    silvia.process_request = original_process

    # 2. Verify SHADOW Intent
    latest_entry = aig_shadow.chain[-1]
    assert latest_entry["event_type"] == "exmail.received"
    trace_id = latest_entry["payload"]["trace_id"]
    assert trace_id is not None

    # 3. Verify downstream events (Guest & Reservation created via workflow)
    # Since we use subscribers, they should have executed synchronously in this test environment
    # We can check the SHADOW ledger for the emitted events
    chain = aig_shadow.chain
    event_types = [e["event_type"] for e in chain]
    assert "nexus.guest.created" in event_types
    assert "nexus.reservation.confirmed" in event_types
    assert "ut.booking.created" in event_types

    # 4. FCE Invoice Finalization
    vvvip_session["nonce"] = "new-nonce-invoice"
    vvvip_session["signature"] = aig_aegis.sign_session(vvvip_session)
    res_invoice = fce.finalize_invoice(
        folio_id="F-SALA-101",
        base_amount=Decimal("1000.00"),
        pax=2,
        nights=4,
        session_context=vvvip_session,
        connection_context=orban_context
    )

    assert res_invoice["status"] == "FINALIZED" if "status" in res_invoice else True
    assert Decimal(str(res_invoice["total"])) > 1000
    assert "mvr_total" in res_invoice

    # 5. Final Audit Chain Validation
    final_chain = aig_shadow.chain
    event_types = [e["event_type"] for e in final_chain]
    assert "sala.invoice.finalized" in event_types
    assert "FINALIZE_INVOICE_PROCESS" in event_types

    # 6. Verify Guarded Path (Tamper Proofing)
    with pytest.raises(RuntimeError):
        # Direct publish blocked
        events.publish("test", {"data": "malicious"})

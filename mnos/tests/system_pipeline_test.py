import pytest
from mnos.modules.exmail.service import exmail_authority
from mnos.shared.execution_guard import guard
from mnos.modules.shadow.service import shadow
from mnos.core.storage.ucloud import ucloud
from mnos.core.security.aegis import aegis
from mnos.core.comms.orban import orban_comms

def test_full_sovereign_pipeline_success():
    """
    Scenario: Ingest ExMAIL -> Execution Guard -> Shadow Commit -> UCloud Write.
    """
    # 1. Setup session with AEGIS signature
    session = {"device_id": "nexus-001", "role": "admin"}
    session["signature"] = aegis.sign_session(session)

    # 2. Ensure ORBAN context is active
    orban_comms.active_secure_tunnel = True

    # 3. Ingest Inbound ExMAIL (Entry point)
    sender = "test@mig.mv"
    subject = "Hardening Request"
    body = "Please update the perimeter."

    response = exmail_authority.ingest_inbound_exmail(
        sender=sender,
        subject=subject,
        body=body,
        session_context=session
    )

    assert response["status"] == "SUCCESS"

    # 4. Verify SHADOW entry (ExMAIL received)
    # The last entry should be 'exmail.received'
    last_block = shadow.chain[-1]
    assert last_block["event_type"] == "exmail.received"
    assert last_block["actor_id"] == "SYSTEM"
    assert "payload" in last_block

    # 5. Execute a module action and write to UCloud
    def vault_action(payload):
        return ucloud.write(payload["key"], payload["data"], payload["session"])

    payload = {
        "key": "reality_config",
        "data": {"status": "HARDENED", "version": "10.0"},
        "session": session
    }

    result = guard.execute_sovereign_action(
        action_type="nexus.security.handshake",
        payload=payload,
        session_context=session,
        execution_logic=vault_action
    )

    assert result["status"] == "SUCCESS"

    # 6. Verify UCloud state
    stored_data = ucloud.read("reality_config", session)
    assert stored_data["status"] == "HARDENED"

    # 7. Verify SHADOW chain integrity
    assert shadow.verify_integrity() is True
    print("[PipelineTest] Full sovereign chain validated successfully.")

def test_pipeline_failure_unsigned_request():
    """Verify that unsigned requests are rejected at ingress."""
    session = {"device_id": "nexus-001"}
    # No signature added

    with pytest.raises(RuntimeError) as excinfo:
        exmail_authority.ingest_inbound_exmail(
            sender="rogue@null.com",
            subject="Attack",
            body="Bypass",
            session_context=session
        )
    assert "EXMAIL_INGRESS_FAILURE" in str(excinfo.value)

def test_pipeline_failure_untrusted_device():
    """Verify that unauthorized devices are blocked from UCloud write."""
    session = {"device_id": "rogue-device"}
    session["signature"] = aegis.sign_session(session)

    def rogue_action(payload):
        return ucloud.write("secret", "data", session)

    with pytest.raises(Exception): # AEGIS will raise SecurityException
        guard.execute_sovereign_action(
            action_type="rogue.event",
            payload={},
            session_context=session,
            execution_logic=rogue_action
        )

if __name__ == "__main__":
    pytest.main([__file__])

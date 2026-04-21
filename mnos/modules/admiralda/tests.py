import pytest
import asyncio
from unittest.mock import MagicMock
from mnos.modules.admiralda.service import AdmiraldaService, AmbiguousCommandError

@pytest.mark.asyncio
async def test_execute_voice_command_success():
    service = AdmiraldaService(db_session=MagicMock())
    result = await service.execute_voice_command(
        transcript="What is the folio balance for room 204?",
        channel="sip",
        session_id="VALID-SESSION",
        caller_id="+9601234567"
    )

    assert result.status == "accepted"
    assert result.intent == "folio.balance_inquiry"
    assert result.target_module == "INN"
    assert result.policy_decision == "allow"
    assert "retrieved" in result.human_message
    assert result.shadow_commit_id.startswith("SHADOW-")
    assert "ADMIRALDA_COMMAND_EXECUTED" in result.events_emitted

@pytest.mark.asyncio
async def test_execute_voice_command_fce_flow():
    service = AdmiraldaService(db_session=MagicMock())
    result = await service.execute_voice_command(
        transcript="Generate a payment link for my stay",
        channel="sip",
        session_id="VALID-SESSION",
        caller_id="+9601234567"
    )

    assert result.status == "accepted"
    assert result.intent == "payment.link_generate"
    assert result.requires_fce is True
    assert result.fce_check_passed is True
    assert "payment_link" in result.execution_payload

@pytest.mark.asyncio
async def test_execute_voice_command_ambiguous_rejection():
    service = AdmiraldaService(db_session=MagicMock())
    result = await service.execute_voice_command(
        transcript="Uh... what?",
        channel="sip",
        session_id="VALID-SESSION",
        caller_id="+9601234567"
    )

    assert result.status == "rejected"
    assert result.reason_code == "AMBIGUOUS_COMMAND"

@pytest.mark.asyncio
async def test_execute_voice_command_aegis_failure():
    service = AdmiraldaService(db_session=MagicMock())
    # Session missing or invalid should trigger failure
    result = await service.execute_voice_command(
        transcript="Folio balance please",
        channel="sip",
        session_id="",
        caller_id="+9601234567"
    )

    assert result.status == "failed"
    assert result.reason_code == "UNHANDLED_EXECUTION_FAILURE"

@pytest.mark.asyncio
async def test_execute_voice_command_voice_match_failure():
    service = AdmiraldaService(db_session=MagicMock())
    # Low voice match score should fail AEGIS step
    result = await service.execute_voice_command(
        transcript="Folio balance please",
        channel="sip",
        session_id="VALID-SESSION",
        caller_id="+9601234567",
        metadata={"voice_match_score": 0.90}
    )

    assert result.status == "failed"
    assert result.reason_code == "UNHANDLED_EXECUTION_FAILURE"

@pytest.mark.asyncio
async def test_execute_voice_command_maintenance_dispatch():
    service = AdmiraldaService(db_session=MagicMock())
    result = await service.execute_voice_command(
        transcript="The air conditioner is broken in room 302",
        channel="sip",
        session_id="VALID-SESSION",
        caller_id="+9601234567"
    )

    assert result.status == "accepted"
    assert result.intent == "maintenance.ticket_create"
    assert result.target_module == "MAINTAIN"
    assert result.execution_payload == {}
    assert "Maintenance ticket created" in result.human_message

@pytest.mark.asyncio
async def test_execute_voice_command_shadow_failure_closed():
    service = AdmiraldaService(db_session=MagicMock())

    # Mock SHADOW failure
    async def mock_shadow_fail(*args, **kwargs):
        from mnos.modules.admiralda.schemas import ShadowCommitResult
        return ShadowCommitResult(success=False)

    service.commit_shadow_record = mock_shadow_fail

    result = await service.execute_voice_command(
        transcript="Folio balance",
        channel="sip",
        session_id="VALID-SESSION"
    )

    assert result.status == "failed"
    assert result.reason_code == "SHADOW_COMMIT_FAILURE"

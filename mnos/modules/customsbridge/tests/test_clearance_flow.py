import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from mnos.modules.customsbridge.schemas.request import ClearanceRequest, OverrideRequest
from mnos.modules.customsbridge.domain.services import CustomsOrchestrator

@pytest.mark.asyncio
async def test_clearance_approved_flow():
    request_data = {
        "request_id": "REQ-2026-0001",
        "container_id": "MSCU1234567",
        "declaration_type": "EXPORT",
        "commodity": "YELLOWFIN_TUNA",
        "origin_site_id": "KANDUOIYGIRI_HUB",
        "mnos_batch_ids": ["B-9982-A", "B-9982-B"],
        "declared_weight": 12500.0,
        "destination_country": "JP",
        "requested_by_officer_id": "CUST-0042"
    }
    request = ClearanceRequest(**request_data)

    mock_db = MagicMock()

    with patch("mnos.modules.customsbridge.domain.services.AquaClient.verify_batches", new_callable=AsyncMock) as mock_aqua, \
         patch("mnos.modules.customsbridge.domain.services.OdysseyClient.validate_yield", new_callable=AsyncMock) as mock_odyssey, \
         patch("mnos.modules.customsbridge.domain.services.FceClient.check_settlement", new_callable=AsyncMock) as mock_fce, \
         patch("mnos.modules.customsbridge.domain.services.EleoneClient.get_risk_score", new_callable=AsyncMock) as mock_eleone, \
         patch("mnos.modules.customsbridge.domain.services.EventsClient.publish_event", new_callable=AsyncMock) as mock_events, \
         patch("mnos.modules.customsbridge.domain.services.ShadowClient.write_record", new_callable=AsyncMock) as mock_shadow, \
         patch("mnos.modules.customsbridge.domain.services.AegisClient.trigger_port_lock", new_callable=AsyncMock) as mock_aegis, \
         patch("mnos.modules.customsbridge.domain.services.SkyGodownClient.check_export_readiness", new_callable=AsyncMock) as mock_skygodown:

        mock_aqua.return_value = {"status": "VERIFIED"}
        mock_odyssey.return_value = {"status": "MATCH"}
        mock_fce.return_value = {"status": "SETTLED"}
        mock_eleone.return_value = {"risk_score": 0.02}
        mock_skygodown.return_value = {"status": "READY"}

        orchestrator = CustomsOrchestrator(mock_db)
        response = await orchestrator.process_clearance_request(request)

        assert response.status == "APPROVED"
        assert response.code == 200
        assert response.clearance_token is not None
        assert response.risk_score == 0.02
        assert mock_db.add.called
        assert mock_db.commit.called

@pytest.mark.asyncio
async def test_clearance_blocked_flow():
    request_data = {
        "request_id": "REQ-2026-0002",
        "container_id": "MSCU1234568",
        "declaration_type": "EXPORT",
        "commodity": "YELLOWFIN_TUNA",
        "mnos_batch_ids": ["B-BAD-ID"],
        "declared_weight": 100.0,
        "requested_by_officer_id": "CUST-0042"
    }
    request = ClearanceRequest(**request_data)

    mock_db = MagicMock()

    with patch("mnos.modules.customsbridge.domain.services.AquaClient.verify_batches", new_callable=AsyncMock) as mock_aqua, \
         patch("mnos.modules.customsbridge.domain.services.OdysseyClient.validate_yield", new_callable=AsyncMock) as mock_odyssey, \
         patch("mnos.modules.customsbridge.domain.services.FceClient.check_settlement", new_callable=AsyncMock) as mock_fce, \
         patch("mnos.modules.customsbridge.domain.services.EleoneClient.get_risk_score", new_callable=AsyncMock) as mock_eleone, \
         patch("mnos.modules.customsbridge.domain.services.EventsClient.publish_event", new_callable=AsyncMock) as mock_events, \
         patch("mnos.modules.customsbridge.domain.services.ShadowClient.write_record", new_callable=AsyncMock) as mock_shadow, \
         patch("mnos.modules.customsbridge.domain.services.AegisClient.trigger_port_lock", new_callable=AsyncMock) as mock_aegis, \
         patch("mnos.modules.customsbridge.domain.services.SkyGodownClient.check_export_readiness", new_callable=AsyncMock) as mock_skygodown:

        mock_aqua.return_value = {"status": "NOT_FOUND"}
        mock_odyssey.return_value = {"status": "MATCH"}
        mock_fce.return_value = {"status": "PENDING"}
        mock_eleone.return_value = {"risk_score": 0.1}
        mock_skygodown.return_value = {"status": "READY"}
        mock_aegis.return_value = {"simulated": True}

        orchestrator = CustomsOrchestrator(mock_db)
        response = await orchestrator.process_clearance_request(request)

        assert response.status == "BLOCKED"
        assert response.code == 403
        assert "BatchID not found or unverified" in response.reasons
        assert "Settlement incomplete" in response.reasons
        assert mock_db.add.called
        assert mock_db.commit.called

@pytest.mark.asyncio
async def test_clearance_review_flow():
    request_data = {
        "request_id": "REQ-2026-0003",
        "container_id": "MSCU1234569",
        "declaration_type": "EXPORT",
        "commodity": "YELLOWFIN_TUNA",
        "mnos_batch_ids": ["B-REVIEW"],
        "declared_weight": 100.0,
        "requested_by_officer_id": "CUST-0042"
    }
    request = ClearanceRequest(**request_data)

    mock_db = MagicMock()

    with patch("mnos.modules.customsbridge.domain.services.AquaClient.verify_batches", new_callable=AsyncMock) as mock_aqua, \
         patch("mnos.modules.customsbridge.domain.services.OdysseyClient.validate_yield", new_callable=AsyncMock) as mock_odyssey, \
         patch("mnos.modules.customsbridge.domain.services.FceClient.check_settlement", new_callable=AsyncMock) as mock_fce, \
         patch("mnos.modules.customsbridge.domain.services.EleoneClient.get_risk_score", new_callable=AsyncMock) as mock_eleone, \
         patch("mnos.modules.customsbridge.domain.services.EventsClient.publish_event", new_callable=AsyncMock) as mock_events, \
         patch("mnos.modules.customsbridge.domain.services.ShadowClient.write_record", new_callable=AsyncMock) as mock_shadow, \
         patch("mnos.modules.customsbridge.domain.services.SkyGodownClient.check_export_readiness", new_callable=AsyncMock) as mock_skygodown:

        mock_aqua.return_value = {"status": "VERIFIED"}
        mock_odyssey.return_value = {"status": "MISMATCH"} # Trigger review
        mock_fce.return_value = {"status": "SETTLED"}
        mock_eleone.return_value = {"risk_score": 0.1}
        mock_skygodown.return_value = {"status": "READY"}

        orchestrator = CustomsOrchestrator(mock_db)
        response = await orchestrator.process_clearance_request(request)

        assert response.status == "REVIEW"
        assert response.code == 202
        assert mock_db.add.call_count >= 3 # Request, Batches, and Review record

@pytest.mark.asyncio
async def test_clearance_eleone_failure_flow():
    request_data = {
        "request_id": "REQ-2026-0004",
        "container_id": "MSCU1234570",
        "declaration_type": "EXPORT",
        "commodity": "YELLOWFIN_TUNA",
        "mnos_batch_ids": ["B-ELEONE-FAIL"],
        "declared_weight": 100.0,
        "requested_by_officer_id": "CUST-0042"
    }
    request = ClearanceRequest(**request_data)

    mock_db = MagicMock()

    with patch("mnos.modules.customsbridge.domain.services.AquaClient.verify_batches", new_callable=AsyncMock) as mock_aqua, \
         patch("mnos.modules.customsbridge.domain.services.OdysseyClient.validate_yield", new_callable=AsyncMock) as mock_odyssey, \
         patch("mnos.modules.customsbridge.domain.services.FceClient.check_settlement", new_callable=AsyncMock) as mock_fce, \
         patch("mnos.modules.customsbridge.domain.services.EleoneClient.get_risk_score", new_callable=AsyncMock) as mock_eleone, \
         patch("mnos.modules.customsbridge.domain.services.EventsClient.publish_event", new_callable=AsyncMock) as mock_events, \
         patch("mnos.modules.customsbridge.domain.services.ShadowClient.write_record", new_callable=AsyncMock) as mock_shadow, \
         patch("mnos.modules.customsbridge.domain.services.SkyGodownClient.check_export_readiness", new_callable=AsyncMock) as mock_skygodown:

        mock_aqua.return_value = {"status": "VERIFIED"}
        mock_odyssey.return_value = {"status": "MATCH"}
        mock_fce.return_value = {"status": "SETTLED"}
        mock_skygodown.return_value = {"status": "READY"}
        # Simulate ELEONE failure
        mock_eleone.return_value = {"status": "ERROR"}

        orchestrator = CustomsOrchestrator(mock_db)
        response = await orchestrator.process_clearance_request(request)

        assert response.status == "REVIEW"
        assert "ELEONE risk scoring unavailable" in response.reasons
        # Verify SHADOW write for failure
        assert any(call.args[0]["event"] == "CUSTOMS_FAILURE" for call in mock_shadow.call_args_list)

@pytest.mark.asyncio
async def test_inspection_unknown_request():
    from mnos.modules.customsbridge.schemas.request import InspectionResult
    result_data = {
        "request_id": "UNKNOWN",
        "inspection_result": "CONFIRMED",
        "officer_id": "CUST-0042"
    }
    result = InspectionResult(**result_data)

    mock_db = MagicMock()
    mock_db.query().filter().first.return_value = None # Request not found

    with patch("mnos.modules.customsbridge.domain.services.EventsClient.publish_event", new_callable=AsyncMock) as mock_events, \
         patch("mnos.modules.customsbridge.domain.services.ShadowClient.write_record", new_callable=AsyncMock) as mock_shadow:

        orchestrator = CustomsOrchestrator(mock_db)
        response = await orchestrator.process_inspection(result)

        assert response["status"] == "FAILED"
        assert response["reason"] == "Request not found"
        assert mock_events.publish_event.called is False
        assert any(call.args[0]["event"] == "CUSTOMS_FAILURE" for call in mock_shadow.call_args_list)

@pytest.mark.asyncio
async def test_clearance_aqua_failure_flow():
    request_data = {
        "request_id": "REQ-2026-0005",
        "container_id": "MSCU1234571",
        "declaration_type": "EXPORT",
        "commodity": "YELLOWFIN_TUNA",
        "mnos_batch_ids": ["B-AQUA-FAIL"],
        "declared_weight": 100.0,
        "requested_by_officer_id": "CUST-0042"
    }
    request = ClearanceRequest(**request_data)

    mock_db = MagicMock()

    with patch("mnos.modules.customsbridge.domain.services.AquaClient.verify_batches", new_callable=AsyncMock) as mock_aqua, \
         patch("mnos.modules.customsbridge.domain.services.ShadowClient.write_record", new_callable=AsyncMock) as mock_shadow:

        # Simulate AQUA failure
        mock_aqua.return_value = {"status": "ERROR"}

        orchestrator = CustomsOrchestrator(mock_db)
        response = await orchestrator.process_clearance_request(request)

        assert response.status == "REVIEW"
        assert "AQUA service unavailable" in response.reasons
        assert any(call.args[0]["event"] == "CUSTOMS_FAILURE" for call in mock_shadow.call_args_list)

@pytest.mark.asyncio
async def test_clearance_fce_failure_flow():
    request_data = {
        "request_id": "REQ-2026-0006",
        "container_id": "MSCU1234572",
        "declaration_type": "EXPORT",
        "commodity": "YELLOWFIN_TUNA",
        "mnos_batch_ids": ["B-FCE-FAIL"],
        "declared_weight": 100.0,
        "requested_by_officer_id": "CUST-0042"
    }
    request = ClearanceRequest(**request_data)

    mock_db = MagicMock()

    with patch("mnos.modules.customsbridge.domain.services.AquaClient.verify_batches", new_callable=AsyncMock) as mock_aqua, \
         patch("mnos.modules.customsbridge.domain.services.OdysseyClient.validate_yield", new_callable=AsyncMock) as mock_odyssey, \
         patch("mnos.modules.customsbridge.domain.services.SkyGodownClient.check_export_readiness", new_callable=AsyncMock) as mock_skygodown, \
         patch("mnos.modules.customsbridge.domain.services.FceClient.check_settlement", new_callable=AsyncMock) as mock_fce, \
         patch("mnos.modules.customsbridge.domain.services.ShadowClient.write_record", new_callable=AsyncMock) as mock_shadow:

        mock_aqua.return_value = {"status": "VERIFIED"}
        mock_odyssey.return_value = {"status": "MATCH"}
        mock_skygodown.return_value = {"status": "READY"}
        # Simulate FCE failure
        mock_fce.return_value = {"status": "ERROR"}

        orchestrator = CustomsOrchestrator(mock_db)
        response = await orchestrator.process_clearance_request(request)

        assert response.status == "REVIEW"
        assert "FCE service unavailable" in response.reasons
        assert any(call.args[0]["event"] == "CUSTOMS_FAILURE" for call in mock_shadow.call_args_list)

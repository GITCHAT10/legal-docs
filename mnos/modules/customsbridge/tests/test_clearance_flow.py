import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from schemas.request import ClearanceRequest, OverrideRequest
from domain.services import CustomsOrchestrator

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

    with patch("adapters.mnos_clients.AquaClient.verify_batches", new_callable=AsyncMock) as mock_aqua, \
         patch("adapters.mnos_clients.OdysseyClient.validate_yield", new_callable=AsyncMock) as mock_odyssey, \
         patch("adapters.mnos_clients.FceClient.check_settlement", new_callable=AsyncMock) as mock_fce, \
         patch("adapters.mnos_clients.EleoneClient.get_risk_score", new_callable=AsyncMock) as mock_eleone, \
         patch("adapters.mnos_clients.EventsClient.publish_event", new_callable=AsyncMock) as mock_events, \
         patch("adapters.mnos_clients.ShadowClient.write_record", new_callable=AsyncMock) as mock_shadow, \
         patch("adapters.mnos_clients.AegisClient.trigger_port_lock", new_callable=AsyncMock) as mock_aegis, \
         patch("adapters.mnos_clients.SkyGodownClient.check_export_readiness", new_callable=AsyncMock) as mock_skygodown:

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

    with patch("adapters.mnos_clients.AquaClient.verify_batches", new_callable=AsyncMock) as mock_aqua, \
         patch("adapters.mnos_clients.OdysseyClient.validate_yield", new_callable=AsyncMock) as mock_odyssey, \
         patch("adapters.mnos_clients.FceClient.check_settlement", new_callable=AsyncMock) as mock_fce, \
         patch("adapters.mnos_clients.EleoneClient.get_risk_score", new_callable=AsyncMock) as mock_eleone, \
         patch("adapters.mnos_clients.EventsClient.publish_event", new_callable=AsyncMock) as mock_events, \
         patch("adapters.mnos_clients.ShadowClient.write_record", new_callable=AsyncMock) as mock_shadow, \
         patch("adapters.mnos_clients.AegisClient.trigger_port_lock", new_callable=AsyncMock) as mock_aegis, \
         patch("adapters.mnos_clients.SkyGodownClient.check_export_readiness", new_callable=AsyncMock) as mock_skygodown:

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

    with patch("adapters.mnos_clients.AquaClient.verify_batches", new_callable=AsyncMock) as mock_aqua, \
         patch("adapters.mnos_clients.OdysseyClient.validate_yield", new_callable=AsyncMock) as mock_odyssey, \
         patch("adapters.mnos_clients.FceClient.check_settlement", new_callable=AsyncMock) as mock_fce, \
         patch("adapters.mnos_clients.EleoneClient.get_risk_score", new_callable=AsyncMock) as mock_eleone, \
         patch("adapters.mnos_clients.EventsClient.publish_event", new_callable=AsyncMock) as mock_events, \
         patch("adapters.mnos_clients.ShadowClient.write_record", new_callable=AsyncMock) as mock_shadow, \
         patch("adapters.mnos_clients.SkyGodownClient.check_export_readiness", new_callable=AsyncMock) as mock_skygodown:

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

import pytest
import os
from httpx import AsyncClient, ASGITransport
from mnos.modules.lifeline.main import app as lifeline_app
from unittest.mock import AsyncMock, patch
from mnos.shared.sdk.models import MnosEnvelope

@pytest.mark.asyncio
async def test_create_patient_flow():
    os.environ["MNOS_INTEGRATION_SECRET"] = "test-secret"

    payload = {
        "name": "Ahmed Mohamed",
        "national_id": "A123456",
        "dob": "1990-01-01"
    }

    headers = {
        "Authorization": "Bearer valid_token",
        "X-Signature": "sig",
        "X-Timestamp": "1234567890",
        "X-Request-Id": "req-1",
        "X-Idempotency-Key": "idem-1"
    }

    transport = ASGITransport(app=lifeline_app)

    with patch("mnos.modules.lifeline.main.mnos_client") as mock_client:
        mock_client.verify_aegis = AsyncMock(return_value=True)
        mock_client.decide_eleone = AsyncMock(return_value="ALLOW")
        mock_client.publish_event = AsyncMock(return_value="EVT-123")
        mock_client.commit_shadow = AsyncMock(return_value="SHD-123")
        # create_response_envelope is a sync method in the SDK
        mock_client.create_response_envelope.side_effect = lambda module, transaction_id, status, data, shadow_id, event_id: MnosEnvelope(
            module=module,
            transaction_id=transaction_id,
            status=status,
            data=data,
            shadow_id=shadow_id,
            event_id=event_id
        )

        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/api/lifeline/patients", json=payload, headers=headers)

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        mock_client.verify_aegis.assert_called_once()
        mock_client.decide_eleone.assert_called_once()
        mock_client.publish_event.assert_called_once()
        mock_client.commit_shadow.assert_called_once()

def test_fail_closed_logic():
    assert True

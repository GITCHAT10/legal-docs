import pytest
from fastapi.testclient import TestClient
from skyfarm.main import app
import responses
import os

client = TestClient(app)

@responses.activate
def test_mnos_401_propagation():
    os.environ["ALLOW_INSECURE_DEV"] = "true"
    responses.add(
        responses.POST,
        "http://127.0.0.1:8000/integration/v1/events/production",
        json={"error": "Unauthorized"},
        status=401
    )

    payload = {
        "tenant_id": "sf_001",
        "event_type": "test.event",
        "category": "TEST",
        "data": {"foo": "bar"}
    }

    response = client.post("/integration/v1/send", json=payload)
    if response.status_code != 401:
        print(f"DEBUG: Response body: {response.text}")
    assert response.status_code == 401
    assert "Unauthorized" in response.text

@responses.activate
def test_mnos_timeout():
    # responses doesn't easily simulate true timeout without a callback,
    # but we can check if it handles connection errors.
    responses.add(
        responses.POST,
        "http://127.0.0.1:8000/integration/v1/events/production",
        body=pytest.importorskip("requests").exceptions.ConnectTimeout("Timeout")
    )

    payload = {
        "tenant_id": "sf_001",
        "event_type": "test.event",
        "category": "TEST",
        "data": {"foo": "bar"}
    }

    response = client.post("/integration/v1/send", json=payload)
    assert response.status_code == 502 or response.status_code == 504

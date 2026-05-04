import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def auth_headers():
    return {
        "X-AEGIS-IDENTITY": "COMMERCE-ADMIN-001",
        "X-AEGIS-DEVICE": "COMMERCE-DEV-001",
        "X-TRACE-ID": "TRACE-COMM-001"
    }

def test_creative_delivery_requires_license(auth_headers):
    payload = {
        "delivery_id": "D1", "order_id": "O1", "asset_hashes": ["h1"],
        "has_license_proof": False, "has_usage_approval_proof": True
    }
    response = client.post("/api/redcoral/commerce/delivery", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "requires license proof" in response.json()["detail"]

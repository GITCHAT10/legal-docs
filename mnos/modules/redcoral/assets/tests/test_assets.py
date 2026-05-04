import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def auth_headers():
    return {
        "X-AEGIS-IDENTITY": "ASSET-ADMIN-001",
        "X-AEGIS-DEVICE": "ASSET-DEV-001",
        "X-TRACE-ID": "TRACE-ASSET-001"
    }

def test_asset_import_license_marking(auth_headers):
    payload = {
        "asset_id": "A1", "project_id": "P1", "category": "PHOTO",
        "source": "THIRD_PARTY", "file_hash": "hash123"
    }
    response = client.post("/api/redcoral/assets/import", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["result"]["license_dependent"] is True

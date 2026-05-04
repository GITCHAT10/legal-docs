import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

def test_unauthorized_header_injection_fails():
    # Attempting to fake a role via headers (if it were possible)
    headers = {
        "X-AEGIS-IDENTITY": "fake-id",
        "X-AEGIS-DEVICE": "fake-device",
        "X-AEGIS-SIGNATURE": "VALID_SIG_FOR_fake-id"
    }
    response = client.post("/imoxon/orders/create", json={"items": [], "amount": 100}, headers=headers)
    # Expected 403 (Forbidden) for invalid identity
    assert response.status_code == 403

def test_sql_injection_attempt_rejected():
    headers = {"X-AEGIS-IDENTITY": "admin' OR '1'='1"}
    response = client.post("/imoxon/suppliers/connect", params={"name": "Test"}, headers=headers)
    assert response.status_code == 403

def test_path_traversal_blocked():
    response = client.get("/imoxon/../../etc/passwd")
    assert response.status_code == 404 # Standard FastAPI behavior

def test_zero_trust_default_deny():
    # Attempt privileged action without any headers
    response = client.post("/imoxon/payouts/release", params={"milestone": "AWARD", "ref_id": "1", "total_amount": 100})
    assert response.status_code == 403

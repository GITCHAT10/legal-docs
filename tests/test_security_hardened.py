from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

def test_missing_headers_rejected():
    response = client.post("/imoxon/suppliers/connect", params={"name": "Test"})
    assert response.status_code == 401
    assert "AEGIS_REQUIRED" in response.json()["detail"]

def test_fake_identity_rejected(admin_headers):
    headers = admin_headers.copy()
    headers["X-AEGIS-IDENTITY"] = "fake-id"
    headers["X-AEGIS-SIGNATURE"] = "VALID_SIG_FOR_fake-id"
    response = client.post("/imoxon/suppliers/connect", params={"name": "Test"}, headers=headers)
    assert response.status_code == 401
    assert "INVALID_IDENTITY" in response.json()["detail"]

def test_unbound_device_rejected(admin_headers):
    # Create another identity
    other_id = identity_core.create_profile({"full_name": "Other", "profile_type": "user"})

    headers = admin_headers.copy()
    headers["X-AEGIS-IDENTITY"] = other_id
    headers["X-AEGIS-SIGNATURE"] = f"VALID_SIG_FOR_{other_id}"
    # device in admin_headers is bound to the admin, not other_id
    response = client.post("/imoxon/suppliers/connect", params={"name": "Test"}, headers=headers)
    assert response.status_code == 403
    assert "DEVICE_BINDING_INVALID" in response.json()["detail"]

def test_authorized_access(admin_headers):
    response = client.post("/imoxon/suppliers/connect", params={"name": "Authorized Supplier"}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Authorized Supplier"
    assert "supplier_id" in response.json()

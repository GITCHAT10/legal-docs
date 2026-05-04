import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def admin_headers(create_security_headers):
    return create_security_headers(full_name="Laundry Admin", profile_type="admin")

@pytest.fixture
def guest_headers(create_security_headers):
    return create_security_headers(full_name="Guest User", profile_type="user")

def test_laundry_workflow_multi_store(admin_headers, guest_headers):
    # 1. Register Stores
    store1_data = {"name": "Male Cleaners", "island": "Male", "owner_id": "OWN-01"}
    resp = client.post("/imoxon/laundry/store/register", json=store1_data, headers=admin_headers)
    assert resp.status_code == 200
    store1_id = resp.json()["id"]

    # 2. Submit Laundry Job
    job_items = [{"service_type": "WASH_FOLD", "qty": 2}]
    resp = client.post(f"/imoxon/laundry/order?store_id={store1_id}", json=job_items, headers=guest_headers)
    assert resp.status_code == 200
    order_id = resp.json()["id"]
    assert resp.json()["status"] == "PICKUP_PENDING"

    # 3. Update status
    resp = client.post(f"/imoxon/laundry/order/update?order_id={order_id}&status=WASHING", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "WASHING"

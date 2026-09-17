import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

@pytest.fixture
def admin_headers():
    uid = identity_core.create_profile({"full_name": "Admin", "profile_type": "admin"})
    did = identity_core.bind_device(uid, {"fingerprint": "adm-hw"})
    identity_core.verify_identity(uid, "SYS")
    return {"X-AEGIS-IDENTITY": uid, "X-AEGIS-DEVICE": did, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"}

@pytest.fixture
def guest_headers():
    uid = identity_core.create_profile({"full_name": "Guest", "profile_type": "guest"})
    did = identity_core.bind_device(uid, {"fingerprint": "gst-phone"})
    return {"X-AEGIS-IDENTITY": uid, "X-AEGIS-DEVICE": did, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{uid}"}

def test_laundry_workflow_multi_store(admin_headers, guest_headers):
    # 1. Register Store
    store_data = {"name": "Maafushi Ultra Wash", "island": "Maafushi", "owner_id": "owner-1"}
    resp = client.post("/imoxon/laundry/store/register", json=store_data, headers=admin_headers)
    assert resp.status_code == 200
    store_id = resp.json()["id"]

    # 2. Guest creates order
    # WASH_FOLD = 50.0 MVR
    items = [{"service_type": "WASH_FOLD", "qty": 2}]
    # Base: 100.0 -> 10% SC (10.0) -> 8% GST (8.8) -> Total 118.8
    resp = client.post(f"/imoxon/laundry/order?store_id={store_id}", json=items, headers=guest_headers)
    assert resp.status_code == 200
    order = resp.json()
    assert order["pricing"]["total"] == 118.8
    assert order["status"] == "PICKUP_PENDING"

    # 3. Update Status to DELIVERED
    order_id = order["id"]
    resp = client.post(f"/imoxon/laundry/order/update?order_id={order_id}&status=DELIVERED", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "DELIVERED"

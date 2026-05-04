import pytest
from fastapi.testclient import TestClient
from main import app, identity_core

client = TestClient(app)

def test_hardened_path():
    # 1. Create Identity
    res = client.post("/imoxon/aegis/identity/create", json={"full_name": "Final Test", "profile_type": "admin"})
    actor_id = res.json()["identity_id"]

    # 2. Bind Device
    res = client.post("/imoxon/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "f1"})
    device_id = res.json()["device_id"]

    headers = {"X-AEGIS-IDENTITY": actor_id, "X-AEGIS-DEVICE": device_id, "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}"}

    # 3. Connect Supplier
    res = client.post("/imoxon/suppliers/connect", params={"name": "S1"}, headers=headers)
    assert res.status_code == 200
    sid = res.json()["supplier_id"]

    # 4. Import Product
    res = client.post("/imoxon/products/import", params={"sid": sid}, json={"name": "Item", "price": 100}, headers=headers)
    assert res.status_code == 200

    # 5. Landed Cost
    res = client.post("/imoxon/pricing/landed-cost", params={"base": 100, "cat": "RETAIL"}, headers=headers)
    assert res.status_code == 200
    assert "total" in res.json()

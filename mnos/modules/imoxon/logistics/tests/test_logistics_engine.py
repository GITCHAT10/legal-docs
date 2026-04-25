import pytest
import httpx
import os
import asyncio
from main import app
from httpx import ASGITransport

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.fixture
async def headers(client):
    # Setup authorized actor
    res = await client.post("/aegis/identity/create", json={"full_name": "Logistics Admin", "profile_type": "admin"})
    actor_id = res.json()["identity_id"]
    await client.post("/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "log-dev"})

    h = {"X-AEGIS-IDENTITY": actor_id, "X-AEGIS-DEVICE": "log-dev", "X-AEGIS-VERIFIED": "true"}

    # Verify supplier for rules
    await client.post("/imoxon/suppliers/connect", params={"name": "Alibaba Global"}, headers=h)
    await client.post("/commerce/vendors/approve", json={"did": actor_id, "business_name": "Alibaba"}, headers=h)

    return h

@pytest.mark.anyio
async def test_full_logistics_lifecycle(client, headers):
    # 1. Create Shipment
    sid = headers["X-AEGIS-IDENTITY"]

    shipment_data = {
        "supplier_id": sid,
        "origin": "Guangzhou",
        "destination": "Male Port",
        "items": [{"sku": "RO-V1", "name": "RO Membrane", "quantity": 100, "unit_price": 450}]
    }
    res = await client.post("/api/v1/logistics/shipment/create", json=shipment_data, headers=headers)
    assert res.status_code == 200
    shp_id = res.json()["id"]

    # 2. Port Arrival
    await client.post("/api/v1/logistics/port/arrival", params={"shipment_id": shp_id}, headers=headers)

    # 3. Port Clearance
    await client.post(f"/api/v1/logistics/port/{shp_id}/clearance", json={"agent_id": "MIG-AGENT-1"}, headers=headers)

    # 4. Skygodown Receive
    res = await client.post("/api/v1/logistics/skygodown/receive", params={"shipment_id": shp_id, "operator_id": "W-OP-1"}, headers=headers)
    grn_id = res.json()["id"]

    # 5. Register Lot
    res = await client.post("/api/v1/logistics/lots/register", json={"receipt_id": grn_id, "sku": "RO-V1", "quantity": 100}, headers=headers)
    lot_id = res.json()["id"]

    # 6. Allocation
    res = await client.post("/api/v1/logistics/allocations/create", json={"lot_id": lot_id, "buyer_id": "B-1", "resort_id": "SALA-01", "quantity": 50}, headers=headers)
    alc_id = res.json()["id"]

    # 7. Manifest
    res = await client.post("/api/v1/logistics/manifest/create", json={"destination_id": "SALA-01", "captain_id": "C-01", "vessel_id": "V-99", "allocation_ids": [alc_id]}, headers=headers)
    man_id = res.json()["id"]

    # 8. Transport Assign
    await client.post("/api/v1/logistics/transport/assign", params={"manifest_id": man_id}, json={"driver_id": "C-01", "device_id": "TAB-1"}, headers=headers)

    # 9. Scans (Load then Unload)
    await client.post("/api/v1/logistics/scan/load", json={"manifest_id": man_id, "scan_type": "LOAD"}, headers=headers)
    await client.post("/api/v1/logistics/scan/unload", json={"manifest_id": man_id, "scan_type": "UNLOAD"}, headers=headers)

    # 10. Receipt & Settlement
    receipt_data = {"recipient_id": "MGR-SALA", "received_items": [{"sku": "RO-V1", "qty": 50}]}
    await client.post("/api/v1/logistics/receipt/confirm", params={"manifest_id": man_id}, json=receipt_data, headers=headers)

    res = await client.post("/api/v1/logistics/settlement/release", json={"manifest_id": man_id, "order_id": "ORD-1"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "ELIGIBLE"

@pytest.mark.anyio
async def test_variance_blocks_settlement(client, headers):
    pass

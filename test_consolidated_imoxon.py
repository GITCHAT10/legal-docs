import httpx
import pytest
from httpx import ASGITransport

from main import app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def actor_headers(client):
    created = await client.post(
        "/imoxon/aegis/identity/create",
        json={"full_name": "Test Admin", "profile_type": "admin"},
    )
    assert created.status_code == 200, created.text
    actor_id = created.json()["identity_id"]

    bound = await client.post(
        "/imoxon/aegis/identity/device/bind",
        params={"identity_id": actor_id},
        json={"fingerprint": "test-dev"},
    )
    assert bound.status_code == 200, bound.text
    device_id = bound.json()["device_id"]

    return {
        "X-AEGIS-IDENTITY": actor_id,
        "X-AEGIS-DEVICE": device_id,
        "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}",
    }


async def connect_supplier(client, actor_headers, name):
    response = await client.post(
        "/imoxon/suppliers/connect",
        params={"name": name},
        headers=actor_headers,
    )
    assert response.status_code == 200, response.text
    return response.json()["supplier_id"]


@pytest.mark.anyio
async def test_supplier_product_import(client, actor_headers):
    sid = await connect_supplier(client, actor_headers, "Test Global")

    res = await client.post(
        "/imoxon/products/import",
        params={"sid": sid},
        json={"name": "Item 1", "price": 100},
        headers=actor_headers,
    )
    assert res.status_code == 200, res.text
    product = res.json()
    assert product["supplier_id"] == sid
    assert product["name"] == "Item 1"
    assert product["status"] == "PENDING_APPROVAL"
    assert product["landed_base"] == pytest.approx(126.5)


@pytest.mark.anyio
async def test_product_approval_required(client, actor_headers):
    from main import catalog

    sid = await connect_supplier(client, actor_headers, "Supplier X")
    imported = await client.post(
        "/imoxon/products/import",
        params={"sid": sid},
        json={"name": "Secret Item", "price": 10},
        headers=actor_headers,
    )
    assert imported.status_code == 200, imported.text
    pid = imported.json()["id"]

    assert pid not in catalog.products

    approved = await client.post(
        "/imoxon/products/approve",
        params={"pid": pid},
        headers=actor_headers,
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "APPROVED"
    assert pid in catalog.products


@pytest.mark.anyio
async def test_landed_cost_calculation():
    from main import fce_core

    result = fce_core.finalize_invoice(126.5, "RESORT_SUPPLY")
    assert result["service_charge"] == 12.65
    assert result["tax_rate"] == 0.17
    assert result["tax_amount"] == 23.66
    assert result["total"] == 162.81


@pytest.mark.anyio
async def test_no_direct_shadow_write():
    from main import shadow_core

    with pytest.raises(PermissionError):
        shadow_core.commit("manual.hack", "rogue-actor", {"data": "rogue"})

import httpx
import pytest
import os
from main import app
from httpx import ASGITransport

@pytest.mark.asyncio
async def test_end_to_end_imoxon(admin_headers):
    print("🚀 STARTING iMOXON CONSOLIDATED E2E SUCCESS TEST")
    print("-" * 60)

    os.environ["NEXGEN_SECRET"] = "imoxon-e2e-final"
    transport = ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Identity Setup (Using fixture)
        headers = admin_headers
        print(f"[1] Using Sovereign Identity: {headers['X-AEGIS-IDENTITY']}")

        # 2. Supplier Connection (Alibaba)
        print("[2] Connecting Global Supplier (Alibaba)...")
        res = await client.post("/imoxon/suppliers/connect", params={"name": "Alibaba Group"}, headers=headers)
        assert res.status_code == 200
        sid = res.json()["supplier_id"]
        print(f"    Supplier ID: {sid}")

        # 3. Product Import
        print("[3] Importing Products (Sourcing Grid)...")
        res = await client.post(f"/imoxon/products/import?sid={sid}", json=[{"name": "Industrial RO Membrane", "price": 450.0}], headers=headers)
        assert res.status_code == 200
        pid = res.json()["products"][0]["id"]
        print(f"    Product ID (Pending): {pid}")

        # 4. Landed Cost Calculation
        print("[4] Calculating Maldives Landed Cost...")
        res = await client.post("/imoxon/pricing/landed-cost?base=450.0&cat=RESORT_SUPPLY", headers=headers)
        assert res.status_code == 200
        pricing = res.json()
        print(f"    Final Landed Price (incl. 17% TGST): {pricing['total']} MVR")

        # 5. Admin Approval
        print("[5] Admin Approval (Audit Trail)...")
        res = await client.post(f"/imoxon/products/approve?pid={pid}", headers=headers)
        assert res.status_code == 200

        # 6. B2B Order (SALA Resort)
        print("[6] SALA Resort B2B Procurement Order...")
        res = await client.post("/imoxon/orders/create", json={
            "items": [{"product_id": pid, "qty": 10}],
            "amount": pricing["total"] * 10
        }, headers=headers)
        assert res.status_code == 200
        order_id = res.json()["id"]
        print(f"    Order ID: {order_id}")

        # 7. Final Integrity Check
        print("[7] Verifying SHADOW Certificate...")
        res = await client.get("/health")
        assert res.status_code == 200
        print(f"    Sovereign Integrity: {res.json()['integrity']}")

    print("-" * 60)
    print("✅ iMOXON CONSOLIDATED E2E SUCCESS")

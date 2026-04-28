import httpx
import asyncio
import json
import sys

async def run_cheval_blanc_test():
    base_url = "http://localhost:8000"

    print("🚀 STARTING LIVE BOOKING TEST: CHEVAL BLANC RANDHELI")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Setup Identity
        print("\nStep 1: Creating Agent Identity...")
        res = await client.post(f"{base_url}/imoxon/aegis/identity/create", json={
            "full_name": "Prestige Luxury Agent",
            "profile_type": "dmc_ta_staff",
            "organization_id": "PRESTIGE-HOLIDAYS"
        })
        identity_id = res.json()["identity_id"]

        print("Step 2: Binding Device...")
        res = await client.post(f"{base_url}/imoxon/aegis/identity/device/bind?identity_id={identity_id}", json={
            "fingerprint": "CHEVAL-TEST-DEVICE-001"
        })
        device_id = res.json()["device_id"]

        headers = {
            "X-AEGIS-IDENTITY": identity_id,
            "X-AEGIS-DEVICE": device_id,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{identity_id}"
        }

        # 2. Trigger High-Value Procurement (Cheval Blanc Villa)
        # Price: 1,000,000 MVR (High Value)
        print("\nStep 3: Creating High-Value Purchase Request for Cheval Blanc...")
        payload = {
            "items": ["Cheval Blanc Randheli - Garden Water Villa (7 Nights)"],
            "amount": 1000000,
            "product_type": "PACKAGE",
            "tax_type": "TOURISM_STANDARD"
        }
        res = await client.post(f"{base_url}/imoxon/orders/create", json=payload, headers=headers)
        if res.status_code != 200:
            print(f"❌ PR Creation Failed: {res.text}")
            sys.exit(1)

        order = res.json()
        order_id = order["id"]
        print(f"✅ PR Created: {order_id}")

        # 3. Approval Flow (Dual Approval Intercept Simulation)
        print("\nStep 4: Approving Order (First Signature)...")
        res = await client.post(f"{base_url}/imoxon/orders/approve?order_id={order_id}", headers=headers)
        order = res.json()
        print(f"Status: {order['status']} (Approvals: {len(order['approvals'])})")

        # Need second approval for > 50k
        print("Step 5: Second Approval (System Admin Signature)...")
        # In this test we use another identity for second signature
        res = await client.post(f"{base_url}/imoxon/aegis/identity/create", json={
            "full_name": "Prestige Finance Director",
            "profile_type": "admin"
        })
        admin_id = res.json()["identity_id"]
        res = await client.post(f"{base_url}/imoxon/aegis/identity/device/bind?identity_id={admin_id}", json={})
        admin_dev = res.json()["device_id"]

        admin_headers = {
            "X-AEGIS-IDENTITY": admin_id,
            "X-AEGIS-DEVICE": admin_dev,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{admin_id}"
        }

        res = await client.post(f"{base_url}/imoxon/orders/approve?order_id={order_id}", headers=admin_headers)
        order = res.json()
        print(f"✅ Final Approval Status: {order['status']}")

        # 4. Finalize Invoice
        print("\nStep 6: Finalizing MIRA Invoice...")
        res = await client.post(f"{base_url}/imoxon/orders/invoice?order_id={order_id}", headers=admin_headers)
        order = res.json()
        pricing = order["pricing"]

        print(f"📊 FINANCIALS (MIRA COMPLIANT):")
        print(f"   Base: {pricing['base_mvr']:,} MVR")
        print(f"   Service Charge (10%): {pricing['service_charge']:,} MVR")
        print(f"   TGST (17%): {pricing['tax_amount']:,} MVR")
        print(f"   TOTAL: {pricing['total_mvr']:,} MVR")

        # Verify Audit Integrity
        res = await client.get(f"{base_url}/health")
        print(f"\n✅ SYSTEM HEALTH: {res.json()['status']} | SHADOW INTEGRITY: {res.json()['integrity']}")

        print("\n🏆 LIVE BOOKING TEST COMPLETE: ROS ACTIVATED.")

if __name__ == "__main__":
    asyncio.run(run_cheval_blanc_test())

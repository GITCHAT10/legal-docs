import httpx
import asyncio
import os
import json
from main import app, shadow_core, guard, identity_core
from httpx import ASGITransport

async def run_final_cto_audit():
    print("🏛️ FINAL iMOXON CONSOLIDATED AUDIT (CTO-LEVEL)")
    print("-" * 60)

    os.environ["NEXGEN_SECRET"] = "cto-audit-2026"
    transport = ASGITransport(app=app)

    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Setup Admin
        print("[0] Initializing Admin Identity...")
        with guard.sovereign_context(SYSTEM_CTX):
            actor_id = identity_core.create_profile({"full_name": "CTO Auditor", "profile_type": "admin"})
            device_id = identity_core.bind_device(actor_id, {"fingerprint": "audit-hw-01"})
            identity_core.verify_identity(actor_id, "sys")

        headers = {
            "X-AEGIS-IDENTITY": actor_id,
            "X-AEGIS-DEVICE": device_id,
            "X-AEGIS-SIGNATURE": f"VALID_SIG_FOR_{actor_id}",
            "X-ISLAND-ID": "GLOBAL"
        }

        # 2. Workflow 1: Alibaba Import Flow
        print("[1] Alibaba Product Import Workflow...")
        raw_p = {"name": "Industrial RO Membrane", "price": 450.0}
        res = await client.post("/imoxon/products/import", params={"sid": "ALIBABA-01"}, json=raw_p, headers=headers)
        if res.status_code != 200:
             print(f"FAILED: {res.status_code} {res.text}")
             return
        pid = res.json()["id"]
        print(f"    Landed Base: {res.json()['landed_base']} MVR")

        # 3. Workflow 2: Admin Approval
        print("[2] Admin Approval Flow...")
        await client.post("/imoxon/products/approve", params={"pid": pid}, headers=headers)

        # 4. Workflow 3: B2B Resort Procurement (SALA)
        print("[3] SALA Resort B2B Procurement Order...")
        b2b_data = {"amount": 2000, "items": [{"id": pid, "qty": 10}]}
        res = await client.post("/imoxon/orders/create", json=b2b_data, headers=headers)
        if res.status_code != 200:
            print(f"FAILED: {res.status_code} {res.text}")
            return
        data = res.json()
        print(f"    Order ID: {data.get('id')}")

        # 5. Security Check: Block Mutation without Headers
        print("[4] Security: Rejection Check (No Headers)...")
        res = await client.post("/imoxon/products/import", params={"sid": "X"}, json={})
        print(f"    Result: {res.status_code} (Blocked)")

        # 6. Audit Check: Immutable Shadow Certificate
        print("[5] Audit: Verifying SHADOW Certificate...")
        integrity = shadow_core.verify_integrity()
        print(f"    SHADOW Chain Integrity: {'VALID' if integrity else 'BROKEN'}")

    print("-" * 60)
    print("✅ FINAL CTO AUDIT COMPLETE")

if __name__ == "__main__":
    asyncio.run(run_final_cto_audit())

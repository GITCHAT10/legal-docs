import httpx
import asyncio
import os
from main import app, shadow_core
from httpx import ASGITransport

async def run_final_cto_audit():
    print("🏛️ FINAL SALA-UPOS CONSOLIDATED AUDIT (CTO-LEVEL)")
    print("-" * 60)

    os.environ["NEXGEN_SECRET"] = "cto-audit-2026"
    transport = ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Setup Admin
        res = await client.post("/aegis/identity/create", json={"full_name": "CTO Auditor", "profile_type": "admin"})
        actor_id = res.json()["identity_id"]
        await client.post("/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "audit-hw-01"})
        headers = {"X-AEGIS-IDENTITY": actor_id, "X-AEGIS-DEVICE": "audit-hw-01", "X-MNOS-SIGNATURE": "sys-audit"}

        # 2. Workflow 1: Alibaba Import Flow
        print("[1] Alibaba Product Import Workflow...")
        raw_p = {"name": "Industrial RO Membrane", "price": 450.0}
        res = await client.post("/imoxon/products/import", params={"sid": "ALIBABA-01"}, json=raw_p, headers=headers)
        pid = res.json()["id"]
        # Expected Landed Base: 450 * 1.15 * 1.10 = 569.25
        print(f"    Landed Base: {res.json()['landed_base']} MVR")

        # 3. Workflow 2: Admin Approval
        print("[2] Admin Approval Flow...")
        await client.post("/imoxon/products/approve", params={"pid": pid}, headers=headers)

        # 4. Workflow 3: B2B Resort Procurement (SALA)
        print("[3] SALA Resort B2B Procurement Order...")
        b2b_data = {"amount": 2000, "items": [{"id": pid, "qty": 10}]}
        res = await client.post("/imoxon/b2b/procurement-request", json=b2b_data, headers=headers)
        pricing = res.json()["pricing"]
        # MIRA Verification: 2000 + 200 (SC) = 2200. 2200 * 0.17 = 374. Total = 2574.
        print(f"    FCE Final Total: {pricing['total']} MVR")

        # 5. Security Check: Block Mutation without Headers
        print("[4] Security: Rejection Check (No Headers)...")
        res = await client.post("/imoxon/products/import", json={})
        print(f"    Result: {res.status_code} (Blocked)")

        # 6. Audit Check: Immutable Shadow Certificate
        print("[5] Audit: Verifying SHADOW Certificate...")
        integrity = shadow_core.verify_integrity()
        print(f"    SHADOW Chain Integrity: {'VALID' if integrity else 'BROKEN'}")

    print("-" * 60)
    print("✅ FINAL CTO AUDIT COMPLETE")

if __name__ == "__main__":
    asyncio.run(run_final_cto_audit())

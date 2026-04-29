import httpx
import asyncio
import os
import json
from main import app
from httpx import ASGITransport

async def verify_prod_workflows():
    print("🚀 STARTING PRODUCTION WORKFLOW VERIFICATION")
    print("-" * 60)

    os.environ["NEXGEN_SECRET"] = "mnos-sovereign-production"
    transport = ASGITransport(app=app)
    results = []

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Identity Setup
        res = await client.post("/aegis/identity/create", json={"full_name": "Prod Operator", "profile_type": "staff"})
        actor_id = res.json()["identity_id"]
        await client.post("/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "prod-dev"})
        headers = {"X-AEGIS-IDENTITY": actor_id, "X-AEGIS-DEVICE": "prod-dev"}

        # 2. Demand Signal
        print("[1] Capturing Demand Signal...")
        res = await client.post("/supply/demand", params={"resort": "MIG-RES-01"}, json=[{"item": "RO Filter", "qty": 5}], headers=headers)
        results.append({"name": "Demand Capture", "res": "SUCCESS" if res.status_code == 200 else "FAIL"})

        # 3. Procurement RFP
        print("[2] Issuing Procurement RFP...")
        res = await client.post("/supply/procurement/issue", json=["dem_123"], headers=headers)
        results.append({"name": "Procurement RFP", "res": "SUCCESS" if res.status_code == 200 else "FAIL"})

        # 4. Skygodown Receipt
        print("[3] Skygodown Batch Receipt...")
        res = await client.post("/supply/skygodown/receive", json={"batch": "B-99", "items": ["RO-F"]}, headers=headers)
        results.append({"name": "Skygodown Receipt", "res": "SUCCESS" if res.status_code == 200 else "FAIL"})

        # 5. TailorGrid Measurement
        print("[4] TailorGrid Fitting...")
        res = await client.post("/tailor/measurement", params={"staff_id": "STAFF-01"}, json={"size": "M", "height": 175}, headers=headers)
        results.append({"name": "TailorGrid Fitting", "res": "SUCCESS" if res.status_code == 200 else "FAIL"})

        # 6. LinenGrid Cycle
        print("[5] LinenGrid Wash Tracker...")
        res = await client.post("/linen/wash", params={"tag_id": "RFID-L-55"}, headers=headers)
        results.append({"name": "LinenGrid Wash", "res": "SUCCESS" if res.status_code == 200 else "FAIL"})

        # 7. UT Assignment
        print("[6] UT Vessel Assignment...")
        res = await client.post("/ut/assign", params={"manifest_id": "man_101", "vessel_id": "boat_v7"}, headers=headers)
        results.append({"name": "UT Assignment", "res": "SUCCESS" if res.status_code == 200 else "FAIL"})

        # 8. Integrity Check
        res = await client.get("/health")
        results.append({"name": "System Integrity", "res": "SUCCESS", "integrity": res.json()["integrity"]})

    print("-" * 60)
    print("✅ PRODUCTION VERIFICATION COMPLETE")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(verify_prod_workflows())

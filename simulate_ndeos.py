import httpx
import asyncio
import os
import json
from main import app, events_core, shadow_core, guard
from httpx import ASGITransport
from mnos.edge.base import EdgeNode

async def simulate_ndeos():
    print("🚀 STARTING N-DEOS DISTRIBUTED SYSTEM SIMULATION")
    print("-" * 60)

    os.environ["NEXGEN_SECRET"] = "ndeos-sim-2026"
    transport = ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Edge Node Initialization (Resort Island)
        print("[1] Initializing Edge Node (SALA Resort)...")
        edge = EdgeNode("MIG-SALA-01", events_core, guard)

        # 2. Offline Mode Simulation
        print("[2] Simulating Island Connectivity Loss (Offline Queueing)...")
        edge.status = "OFFLINE"
        res = edge.execute_local("imoxon.supply.demand", {"identity_id": "OP-01", "device_id": "tab-1"}, None, {"resort": "SALA", "items": []})
        print(f"    Action Status: {res['status']}")

        # 3. Connectivity Recovery & Sync
        print("[3] Connectivity Restored (Syncing to Core)...")
        edge.status = "ONLINE"
        edge.sync_to_core()

        # 4. Distributed Event Streaming (Partitioning)
        print("[4] Publishing Partitioned Events (Male Atoll vs Port)...")
        # Standard actor setup for guard
        res = await client.post("/aegis/identity/create", json={"full_name": "Grid Admin", "profile_type": "admin"})
        actor_id = res.json()["identity_id"]
        await client.post("/aegis/identity/device/bind", params={"identity_id": actor_id}, json={"fingerprint": "adm-dev"})
        headers = {"X-AEGIS-IDENTITY": actor_id, "X-AEGIS-DEVICE": "adm-dev", "X-ISLAND-ID": "MIG-SALA-01", "X-MNOS-SIGNATURE": "sig-valid"}

        # Use core API which publishes to partitioned bus
        await client.post("/imoxon/supply/demand", json={"resort": "SALA", "items": []}, headers=headers)

        # 5. Legal Audit Bundle
        print("[5] Generating Legal Audit Bundle (Court Grade)...")
        bundle = shadow_core.generate_legal_audit_bundle(0, len(shadow_core.chain)-1)
        print(f"    Bundle Certification Hash: {bundle['manifest']['certification_hash']}")

    print("-" * 60)
    print("✅ N-DEOS SIMULATION SUCCESSFUL")

if __name__ == "__main__":
    asyncio.run(simulate_ndeos())

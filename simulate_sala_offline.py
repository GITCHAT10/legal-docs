import sys
import os
import uuid
from datetime import datetime, UTC

# Ensure we can import from mnos
sys.path.append(os.getcwd())

from main import app, identity_core, guard, bpe, shadow_core, identity_gateway

def simulate():
    print("🚀 STARTING SALA PILOT: SCENARIO B (OFFLINE SYNC)")

    SYSTEM_CTX = {"identity_id": "SYSTEM", "role": "admin", "realm": "SYSTEM"}

    with guard.sovereign_context(SYSTEM_CTX):
        staff_id = identity_core.create_profile({"full_name": "SALA Front Desk", "profile_type": "staff"})
        device_id = identity_core.bind_device(staff_id, {"fingerprint": "sala-offline-01"})
        identity_core.verify_identity(staff_id, "mig-onboarding")

    staff_ctx = {"identity_id": staff_id, "device_id": device_id, "role": "staff", "realm": "API_DIRECT"}

    # 1. Simulate Offline Transactions
    offline_txs = [
        {
            "timestamp": datetime.now(UTC).isoformat(),
            "amount": 250.0,
            "items": [{"id": "COFFEE", "qty": 2}]
        },
        {
            "timestamp": datetime.now(UTC).isoformat(),
            "amount": 1200.0,
            "items": [{"id": "EXCURSION_SANDBANK", "qty": 1}]
        }
    ]
    print(f"📥 Recorded {len(offline_txs)} transactions in Local WAL.")

    # 2. Reconnect and Sync
    print("📡 RECONNECTING... Triggering BPE Offline Sync...")

    sync_result = guard.execute_sovereign_action(
        "bpe.offline_sync",
        staff_ctx,
        bpe.sync_offline_batch,
        "SALA_MERCHANT_01", offline_txs
    )

    print(f"✔ Sync Complete: {sync_result['synced_count']} records pushed to SHADOW.")

    # 3. ORCA Dashboard Verification
    print("📊 Verifying ORCA Dashboard Sync...")
    identity_gateway.sessions["SALA-OFFLINE-SESSION"] = staff_ctx

    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = client.get("/orca/dashboard/summary", headers={"X-AEGIS-SESSION": "SALA-OFFLINE-SESSION"})
    if response.status_code == 200:
        data = response.json()
        metrics = data["metrics"]
        print(f"✔ Dashboard Data Found: Synced Offline={metrics['synced_offline_records']}")
        if metrics['synced_offline_records'] >= 2:
            print("✔ OFFLINE SYNC VISIBLE IN ORCA: OK")
        else:
            print(f"❌ OFFLINE SYNC NOT VISIBLE: Found {metrics['synced_offline_records']}")
    else:
        print(f"❌ Dashboard Failed: {response.status_code}")

    print("🏁 SCENARIO B COMPLETE")

if __name__ == "__main__":
    simulate()

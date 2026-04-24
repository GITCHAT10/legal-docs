import requests
import time
import json
import uuid
import os
from datetime import datetime, timezone
import hmac
import hashlib

SKYFARM_URL = "http://localhost:8001"
MNOS_URL = "http://localhost:8000"

def run_simulation():
    print("Starting FULL SKYFARM Engine Operating Loop Simulation...")
    tenant_id = "sf_maldives_001"
    secret = "production_ready_secret"

    # 1. Marine Intake
    print("\n[Marine] Logging Fish Intake...")
    catch_data = {"vessel_id": "v123", "species": "Yellowfin Tuna", "weight": 52.5, "location": "Zone 4", "tenant_id": tenant_id}
    resp = requests.post(f"{SKYFARM_URL}/api/v1/marine/catch", json=catch_data)
    catch = resp.json()
    print(f"Result: {catch}")

    # 2. Grading
    print("\n[Marine] Grading Catch...")
    grade_data = {"catch_id": catch["id"], "grade": "A+", "tenant_id": tenant_id}
    resp = requests.post(f"{SKYFARM_URL}/api/v1/marine/grade", json=grade_data)
    print(f"Result: {resp.json()}")

    # 3. Trace: Digital Twin
    print("\n[Trace] Creating Digital Twin...")
    twin_data = {"item_id": catch["id"], "actor_id": "inspector_01", "metadata": {"origin": "Male", "method": "Handline"}}
    resp = requests.post(f"{SKYFARM_URL}/api/v1/trace/twin", json=twin_data)
    print(f"Result: {resp.json()}")

    # 4. Agri: Harvest
    print("\n[Agri] Logging Farm Harvest...")
    harvest_data = {"facility_id": "f456", "crop_type": "Lettuce", "quantity": 100, "unit": "kg", "tenant_id": tenant_id}
    resp = requests.post(f"{SKYFARM_URL}/api/v1/agri/harvest", json=harvest_data)
    harvest = resp.json()
    print(f"Result: {harvest}")

    # 5. Production: Create Batch
    print("\n[Production] Creating Batch...")
    batch_data = {"source_ids": [catch["id"], harvest["id"]], "tenant_id": tenant_id}
    resp = requests.post(f"{SKYFARM_URL}/api/v1/production/batch", json=batch_data)
    batch = resp.json()
    print(f"Result: {batch}")

    # 6. Logistics Move
    print("\n[Logistics] Moving Batch to Airport...")
    log_data = {"batch_id": batch["id"], "status": "DISPATCHED", "origin": "Male Port", "destination": "Velana Airport", "tenant_id": tenant_id}
    resp = requests.post(f"{SKYFARM_URL}/api/v1/logistics/event", json=log_data)
    print(f"Result: {resp.json()}")

    # 7. Trace: Custody Transfer
    print("\n[Trace] Recording Custody Transfer to Logistics...")
    transfer_data = {"item_id": batch["id"], "from_actor": "farm_ops", "to_actor": "logistics_team"}
    resp = requests.post(f"{SKYFARM_URL}/api/v1/trace/transfer", json=transfer_data)
    print(f"Result: {resp.json()}")

    # 8. Restaurant Order
    print("\n[Restaurant] Creating Guest Order...")
    order_data = {"facility_id": "inn_01", "items": [{"name": "Seared Tuna Salad", "price": 45.0}], "total_amount": 45.0}
    resp = requests.post(f"{SKYFARM_URL}/api/v1/restaurant/order", json=order_data)
    print(f"Result: {resp.json()}")

    # 9. Retail Sale
    print("\n[Retail] Recording Deli Sale...")
    sale_data = {"store_id": "deli_01", "items": [{"product_id": "lettuce_pack", "price": 12.0}], "total_amount": 12.0}
    resp = requests.post(f"{SKYFARM_URL}/api/v1/retail/sale", json=sale_data)
    print(f"Result: {resp.json()}")

    # 10. Finance: Payout Approval
    print("\n[Finance] Approving Fisherman Payout...")
    pay_req = {"amount": 5000.0, "tenant_id": tenant_id, "reference_id": catch["id"]}
    resp = requests.post(f"{SKYFARM_URL}/api/v1/finance/payment", json=pay_req)
    print(f"Payout Result: {resp.json()}")

    # 11. Integration: Verify Outbox Sync
    print("\n[Integration] Verifying MNOS Sync via Outbox Worker (Wait 10s)...")
    time.sleep(10)

    print("\n[Verification] Checking MNOS received events...")
    try:
        resp = requests.get(f"{MNOS_URL}/mnos/integration/v1/health")
        print(f"MNOS Health: {resp.json()}")
    except:
        print("MNOS connection failed")

    print("\nSimulation Finished.")

if __name__ == "__main__":
    run_simulation()

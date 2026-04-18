import requests
import time
import json
import uuid

SKYFARM_URL = "http://localhost:8001"
MNOS_URL = "http://localhost:8000"

def run_simulation():
    print("Starting SKYFARM Engine Simulation...")
    tenant_id = "sf_maldives_001"

    # 1. Marine: Fish Caught
    print("\n[Marine] Logging Fish Caught...")
    catch_data = {"vessel_id": "v123", "species": "Yellowfin Tuna", "weight": 52.5, "location": "Zone 4"}
    resp = requests.post(f"{SKYFARM_URL}/marine/catch", json=catch_data)
    catch = resp.json()
    print(f"Result: {catch}")

    # 2. Agri: Harvest Completed
    print("\n[Agri] Logging Harvest Completed...")
    harvest_data = {"facility_id": "f456", "crop_type": "Lettuce", "quantity": 100, "unit": "kg"}
    resp = requests.post(f"{SKYFARM_URL}/agri/harvest", json=harvest_data)
    harvest = resp.json()
    print(f"Result: {harvest}")

    # 3. Production: Create Batch
    print("\n[Production] Creating Batch...")
    batch_data = {"source_ids": [catch["id"], harvest["id"]]}
    resp = requests.post(f"{SKYFARM_URL}/production/batch", json=batch_data)
    batch = resp.json()
    print(f"Result: {batch}")

    # 4. Logistics: Dispatch Event
    print("\n[Logistics] Dispatching Batch...")
    log_data = {"batch_id": batch["id"], "status": "DISPATCHED", "origin": "Male Port", "destination": "Velana Airport"}
    resp = requests.post(f"{SKYFARM_URL}/logistics/event", json=log_data)
    print(f"Result: {resp.json()}")

    # 5. Finance: Capture Payment
    print("\n[Finance] Capturing Payment...")
    pay_data = {"amount": 5000.0, "reference_id": batch["id"], "currency": "USD"}
    resp = requests.post(f"{SKYFARM_URL}/finance/payment", json=pay_data)
    print(f"Result: {resp.json()}")

    # 6. Trace: Record Update
    print("\n[Trace] Recording Trace Update...")
    trace_data = {"item_id": batch["id"], "action": "TRACE_UPDATED", "actor_id": "op_01", "metadata": {"temp": "4C"}}
    resp = requests.post(f"{SKYFARM_URL}/trace/record", json=trace_data)
    print(f"Result: {resp.json()}")

    # 7. Integration: Send to MNOS
    print("\n[Integration] Sending Production Sync to MNOS.EVENTS...")
    sync_data = {
        "event_id": f"evt_{uuid.uuid4().hex[:6]}",
        "tenant_id": tenant_id,
        "event_type": "BATCH_CREATED",
        "category": "production",
        "data": batch
    }
    resp = requests.post(f"{SKYFARM_URL}/integration/send", json=sync_data)
    print(f"MNOS Response: {resp.json()}")

    print("\n[Integration] Sending Security Audit to MNOS.AEGIS...")
    audit_data = {
        "event_id": f"evt_{uuid.uuid4().hex[:6]}",
        "tenant_id": tenant_id,
        "event_type": "SECURITY_AUDIT",
        "category": "aegis",
        "data": {"status": "all_clear", "node": "SF-NODE-01"}
    }
    resp = requests.post(f"{SKYFARM_URL}/integration/send", json=audit_data)
    print(f"MNOS Aegis Response: {resp.json()}")

    print("\nSimulation Finished.")

if __name__ == "__main__":
    run_simulation()

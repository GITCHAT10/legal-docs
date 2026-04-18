import requests
import time
import json
from skyfarm.integration.service import create_integration_event

MNOS_URL = "http://localhost:8000"

def run_simulation():
    print("Starting SKYFARM to MNOS Integration Simulation...")

    # 1. Identity Sync
    print("Step 1: Syncing Identity (Vessel)...")
    entity_data = {"id": "v123", "name": "Ocean Voyager", "type": "vessel", "owner_id": "cap_01"}
    event = create_integration_event("evt_001", "sf_maldives_001", "ENTITY_CREATED", entity_data)
    try:
        resp = requests.post(f"{MNOS_URL}/integration/v1/entities", json=event.dict())
        print(f"Response: {resp.status_code} - {resp.json()}")
    except Exception as e:
        print(f"Failed to connect to MNOS: {e}")
        return

    # 2. Production Event
    print("\nStep 2: Pushing Production Event...")
    prod_data = {"batch_id": "batch_88", "item": "Tuna", "weight": 450, "unit": "kg"}
    event = create_integration_event("evt_002", "sf_maldives_001", "BATCH_CREATED", prod_data)
    resp = requests.post(f"{MNOS_URL}/integration/v1/events/production", json=event.dict())
    print(f"Response: {resp.status_code} - {resp.json()}")

    # 3. Logistics Event
    print("\nStep 3: Pushing Logistics Event...")
    log_data = {"batch_id": "batch_88", "status": "dispatched", "origin": "Male", "destination": "Resort X"}
    event = create_integration_event("evt_003", "sf_maldives_001", "DISPATCHED", log_data)
    resp = requests.post(f"{MNOS_URL}/integration/v1/events/logistics", json=event.dict())
    print(f"Response: {resp.status_code} - {resp.json()}")

    # 4. Financial Event
    print("\nStep 4: Pushing Financial Event...")
    fin_data = {"invoice_id": "inv_999", "amount": 1200.50, "currency": "USD", "type": "batch_sold"}
    event = create_integration_event("evt_004", "sf_maldives_001", "BATCH_SOLD", fin_data)
    resp = requests.post(f"{MNOS_URL}/integration/v1/events/finance", json=event.dict())
    print(f"Response: {resp.status_code} - {resp.json()}")

    # 5. Pull Policy
    print("\nStep 5: Pulling Policies from MNOS...")
    resp = requests.get(f"{MNOS_URL}/mnos/v1/policies/skyfarm")
    print(f"Response: {resp.status_code} - {resp.json()}")

    print("\nSimulation Finished.")

if __name__ == "__main__":
    run_simulation()

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
    print("Starting Hardened SKYFARM Engine Simulation...")
    tenant_id = "sf_maldives_001"
    secret = "production_ready_secret"

    # 1. Marine: Fish Intake
    print("\n[Marine] Logging Fish Intake...")
    catch_data = {"vessel_id": "v123", "species": "Yellowfin Tuna", "weight": 52.5, "location": "Zone 4", "tenant_id": tenant_id}
    resp = requests.post(f"{SKYFARM_URL}/api/v1/marine/catch", json=catch_data)
    catch = resp.json()
    print(f"Result: {catch}")

    # 2. Agri: Harvest
    print("\n[Agri] Logging Farm Harvest...")
    harvest_data = {"facility_id": "f456", "crop_type": "Lettuce", "quantity": 100, "unit": "kg", "tenant_id": tenant_id}
    resp = requests.post(f"{SKYFARM_URL}/api/v1/agri/harvest", json=harvest_data)
    harvest = resp.json()
    print(f"Result: {harvest}")

    # 3. Direct Integration Sync (to show hardening and canonical signing)
    print("\n[Integration] Syncing Events to MNOS via Integration Router...")

    event_id = f"evt_{uuid.uuid4().hex}"
    idem_key = f"idem_{uuid.uuid4().hex}"
    # Ensure timestamp has no microseconds and ends with Z for simplicity, or just use isoformat
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    request_id = str(uuid.uuid4())

    body = {
        "event_id": event_id,
        "source": "skyfarm",
        "tenant_id": tenant_id,
        "type": "fish.intake.recorded",
        "timestamp": timestamp,
        "data": catch
    }

    body_json = json.dumps(body, sort_keys=True)
    body_bytes = body_json.encode()
    body_hash = hashlib.sha256(body_bytes).hexdigest()

    method = "POST"
    path = "/mnos/integration/v1/events"
    canonical = f"{method}\n{path}\n{timestamp}\n{request_id}\n{body_hash}"
    signature = hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()

    headers = {
        "X-Request-Id": request_id,
        "X-Idempotency-Key": idem_key,
        "X-Timestamp": timestamp,
        "X-Signature": signature,
        "Content-Type": "application/json"
    }

    print(f"Sending signed event to MNOS (X-Request-Id: {request_id})...")
    resp = requests.post(f"{MNOS_URL}{path}", data=body_bytes, headers=headers)
    print(f"MNOS Response: {resp.json()}")

    # 4. Test Idempotency
    print("\n[Integration] Testing Idempotency (Sending same request again)...")
    resp = requests.post(f"{MNOS_URL}{path}", data=body_bytes, headers=headers)
    print(f"MNOS Idempotency Response: {resp.json()}")

    print("\nSimulation Finished.")

if __name__ == "__main__":
    run_simulation()

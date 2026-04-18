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

    # 1. Marine: Fish Intake (Valid)
    print("\n[Marine] Logging Valid Fish Intake...")
    catch_data = {"vessel_id": "v123", "species": "Yellowfin Tuna", "weight": 52.5, "location": "Zone 4", "tenant_id": tenant_id}
    resp = requests.post(f"{SKYFARM_URL}/api/v1/marine/catch", json=catch_data)
    catch = resp.json()
    print(f"Result: {catch}")

    # 2. Marine: Fish Intake (Invalid Temp - EPIC 3)
    print("\n[Marine] Logging Invalid Fish Intake (High Temp)...")
    bad_catch_data = {**catch_data, "temperature_c": 5.5}
    resp = requests.post(f"{SKYFARM_URL}/api/v1/marine/catch", json=bad_catch_data)
    print(f"Response: {resp.status_code} - {resp.json()}")

    # 3. Finance: Generate Invoice (EPIC 2)
    print("\n[Finance] Generating Invoice (Maldives Pricing)...")
    inv_req = {"base_price": 1000.0, "reference_id": catch["id"]}
    resp = requests.post(f"{SKYFARM_URL}/api/v1/finance/invoice/generate", json=inv_req)
    invoice = resp.json()
    print(f"Invoice: {invoice}")

    # 4. Finance: Create Payout (EPIC 2)
    print("\n[Finance] Creating Payout Batch...")
    pay_req = {"amount": 5000.0, "tenant_id": tenant_id}
    resp = requests.post(f"{SKYFARM_URL}/api/v1/finance/payout/create", json=pay_req)
    print(f"Payout Result: {resp.json()}")

    # 5. Integration: Direct Sync with Canonical Signing (EPIC 1)
    print("\n[Integration] Syncing Event to MNOS with Canonical Signing...")
    event_id = f"evt_{uuid.uuid4().hex}"
    idem_key = f"idem_{uuid.uuid4().hex}"
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

    resp = requests.post(f"{MNOS_URL}{path}", data=body_bytes, headers=headers)
    print(f"MNOS Response: {resp.json()}")

    # 6. Test Idempotency
    print("\n[Integration] Testing Idempotency...")
    resp = requests.post(f"{MNOS_URL}{path}", data=body_bytes, headers=headers)
    print(f"MNOS Idempotency Response: {resp.json()}")

    print("\nSimulation Finished.")

if __name__ == "__main__":
    run_simulation()

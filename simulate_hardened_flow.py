import requests
import hashlib
import hmac
import time
import json

SECRET = "mnos-production-secret"
GATEWAY_URL = "http://localhost:8000"

def sign_request(method, path, timestamp, idempotency_key, body):
    body_hash = hashlib.sha256(body.encode()).hexdigest()
    canonical = f"{method}|{path}|{timestamp}|{idempotency_key}|{body_hash}"
    return hmac.new(SECRET.encode(), canonical.encode(), hashlib.sha256).hexdigest()

def run():
    print("🚀 Starting End-to-End Hardened Flow Simulation...")

    timestamp = str(time.time())
    idempotency = "tx-12345"
    path = "/api/v1/eleone/decide"
    body = json.dumps({"action": "APPROVE", "payload": {"item": "tuna_batch_01"}})

    signature = sign_request("POST", path, timestamp, idempotency, body)

    headers = {
        "X-Signature": signature,
        "X-Timestamp": timestamp,
        "X-Idempotency-Key": idempotency,
        "Content-Type": "application/json"
    }

    print(f"1. Sending signed request to Gateway: {path}")
    resp = requests.post(f"{GATEWAY_URL}{path}", headers=headers, data=body)
    print(f"Response: {resp.status_code} | {resp.text}")

    time.sleep(2) # Wait for worker

    print("\n2. Verifying SHADOW Integrity...")
    shadow_resp = requests.get("http://localhost:8002/verify-integrity")
    print(f"Shadow Status: {shadow_resp.json()}")

if __name__ == "__main__":
    run()

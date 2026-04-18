import requests
import json
import hmac
import hashlib
from datetime import datetime, timezone
import uuid
import time
import os

SECRET_KEY = os.getenv("MNOS_INTEGRATION_SECRET", "dev_fallback_secret")
MNOS_URL = "http://localhost:8000/fuel/request"

def generate_canonical_string(method: str, path: str, timestamp: str, request_id: str, body_bytes: bytes) -> str:
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    return f"{method.upper()}\n{path}\n{timestamp}\n{request_id}\n{body_hash}"

def sign_request(method, path, timestamp, request_id, body):
    body_bytes = json.dumps(body).encode()
    canonical = generate_canonical_string(method, path, timestamp, request_id, body_bytes)
    return hmac.new(SECRET_KEY.encode(), canonical.encode(), hashlib.sha256).hexdigest()

def send_fuel_request(flight_id, aircraft_id, amount, operator_id):
    request_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    body = {
        "flight_id": flight_id,
        "aircraft_id": aircraft_id,
        "fuel_amount": amount,
        "operator_id": operator_id,
        "timestamp": timestamp
    }

    signature = sign_request("POST", "/fuel/request", timestamp, request_id, body)

    headers = {
        "X-Request-Id": request_id,
        "X-Idempotency-Key": str(uuid.uuid4()),
        "X-Signature": signature,
        "X-Timestamp": timestamp,
        "Content-Type": "application/json"
    }

    print(f"\n🚀 Sending Fuel Request: {flight_id} for {amount}L")
    response = requests.post(MNOS_URL, json=body, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

if __name__ == "__main__":
    print("🧪 STARTING FUEL FLOW TEST...")

    # 1. Valid Request (APPROVE)
    send_fuel_request("FL-777", "AC-101", 500, "OP-ALPHA")

    time.sleep(2) # Wait for worker and edge node

    # 2. Invalid Flight ID (DENY by AEGIS)
    send_fuel_request("INVALID-777", "AC-101", 500, "OP-ALPHA")

    time.sleep(2)

    # 3. Blacklisted Operator (DENY by FCE)
    send_fuel_request("FL-777", "AC-101", 500, "BLACKLIST-EVIL")

    time.sleep(2)

    # 4. Large Amount (DENY by FCE)
    send_fuel_request("FL-777", "AC-101", 5000, "OP-ALPHA")

    print("\n✅ TEST SUITE FINISHED.")

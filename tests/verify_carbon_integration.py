import requests
import json
import uuid
import hmac
import hashlib
from datetime import datetime, timezone
import os

def generate_headers(method, path, body, secret):
    request_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    # EXACT same serialization as what reaches the verifier
    body_json = json.dumps(body, separators=(',', ':'), sort_keys=True)
    body_hash = hashlib.sha256(body_json.encode()).hexdigest()

    canonical = f"{method.upper()}\n{path}\n{timestamp}\n{request_id}\n{body_hash}"
    signature = hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()

    return {
        "X-Request-Id": request_id,
        "X-Timestamp": timestamp,
        "X-Signature": signature,
        "Content-Type": "application/json"
    }

def test_carbon_retire():
    print("Testing Carbon Retire Integration...")
    secret = "test_secret"
    os.environ["SKYFARM_INTEGRATION_SECRET"] = secret
    base_url = "http://127.0.0.1:8001"

    path = "/integration/v1/carbon/retire"
    payload = {
        "guest_name": "Aman Guest 001",
        "amount_kg": 14.5,
        "correlation_id": "corr-123"
    }

    headers = generate_headers("POST", path, payload, secret)

    try:
        resp = requests.post(f"{base_url}{path}", json=payload, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")

        assert resp.status_code == 200
        assert resp.json()["status"] == "SUCCESS"
        assert "audit_id" in resp.json()
        print("✅ Carbon Retire Test PASSED")
    except Exception as e:
        print(f"❌ Carbon Retire Test FAILED: {str(e)}")

if __name__ == "__main__":
    test_carbon_retire()

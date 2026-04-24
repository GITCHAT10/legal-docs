import requests
import json
import uuid
import hmac
import hashlib
from datetime import datetime, timezone
import os

def generate_headers(method, path, body, secret):
    request_id = str(uuid.uuid4())
    idempotency_key = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    # Body is sent as JSON. verifier reads body_bytes.
    # We must ensure the byte content matches what the verifier will see.
    # FastAPI reads the raw body. requests.post(json=payload) sends compact JSON.
    body_json = json.dumps(body, separators=(',', ':'))
    body_hash = hashlib.sha256(body_json.encode()).hexdigest()

    canonical = f"{method.upper()}\n{path}\n{timestamp}\n{request_id}\n{body_hash}"
    signature = hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()

    return {
        "X-Request-Id": request_id,
        "X-Idempotency-Key": idempotency_key,
        "X-Timestamp": timestamp,
        "X-Signature": signature,
        "Content-Type": "application/json"
    }

def verify():
    print("Starting MNOS Compliance Verification...")
    secret = os.getenv("MNOS_INTEGRATION_SECRET", "test_secret")
    base_url = "http://127.0.0.1:8000"

    results = {}

    # 1. Ingestion Compliance
    try:
        path = "/integration/v1/events/production"
        payload = {"source": "skyfarm", "tenant_id": "sf_01", "type": "VERIFY", "data": {"status": "ok"}}
        headers = generate_headers("POST", path, payload, secret)
        # Use data=body_bytes to be 100% sure of the content sent
        body_bytes = json.dumps(payload, separators=(',', ':')).encode()
        resp = requests.post(f"{base_url}{path}", data=body_bytes, headers=headers, timeout=5)
        if resp.status_code == 200:
            results["Ingestion API"] = "PASS"
        else:
            results["Ingestion API"] = f"FAIL ({resp.status_code} - {resp.text})"
    except Exception as e:
        results["Ingestion API"] = f"FAIL ({str(e)})"

    # 2. Secret Enforcement
    try:
        resp = requests.get(f"{base_url}/mnos/integration/v1/health", timeout=5)
        mode = resp.json().get("data", {}).get("mode")
        results["Secret Enforcement"] = "PASS" if mode == "enforced" else f"FAIL (Mode: {mode})"
    except Exception as e:
        results["Secret Enforcement"] = f"FAIL ({str(e)})"

    # 3. Policy Determinism
    try:
        path = "/integration/v1/events/production"
        payload = {"source": "skyfarm", "tenant_id": "sf_01", "type": "POLICY", "data": {}}

        headers1 = generate_headers("POST", path, payload, secret)
        body1 = json.dumps(payload, separators=(',', ':')).encode()
        r1 = requests.post(f"{base_url}{path}", data=body1, headers=headers1).json()

        headers2 = generate_headers("POST", path, payload, secret)
        body2 = json.dumps(payload, separators=(',', ':')).encode()
        r2 = requests.post(f"{base_url}{path}", data=body2, headers=headers2).json()

        results["Policy Determinism"] = "PASS" if r1.get("decision") == r2.get("decision") else f"FAIL ({r1.get('decision')} != {r2.get('decision')})"
    except Exception as e:
        results["Policy Determinism"] = f"FAIL ({str(e)})"

    # 4. Policy Rejection
    try:
        path = "/integration/v1/events/production"
        payload = {"source": "skyfarm", "tenant_id": "sf_01", "type": "POLICY", "data": {"test_deny": True}}
        headers = generate_headers("POST", path, payload, secret)
        body = json.dumps(payload, separators=(',', ':')).encode()
        resp = requests.post(f"{base_url}{path}", data=body, headers=headers)
        if resp.status_code == 403:
            results["Policy Rejection"] = "PASS"
        else:
            results["Policy Rejection"] = f"FAIL ({resp.status_code})"
    except Exception as e:
        results["Policy Rejection"] = f"FAIL ({str(e)})"

    print("\nCompliance Summary:")
    print("-" * 30)
    for cat, res in results.items():
        print(f"{cat:<20}: {res}")
    print("-" * 30)

if __name__ == "__main__":
    verify()

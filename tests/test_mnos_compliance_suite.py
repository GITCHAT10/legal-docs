import pytest
from fastapi.testclient import TestClient
from mnos.main import app
from mnos.core.config import config
import hmac
import hashlib
import json
import uuid
from datetime import datetime, timezone

client = TestClient(app)

# Use the actual SECRET_KEY from config since it's loaded from env
SECRET_KEY = config["MNOS_INTEGRATION_SECRET"]

def generate_headers(method, path, body, request_id=None, idempotency_key=None, timestamp=None):
    request_id = request_id or str(uuid.uuid4())
    idempotency_key = idempotency_key or str(uuid.uuid4())
    timestamp = timestamp or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    # Body in event is a Pydantic model in the endpoint, so we dump it exactly as FastAPI does
    body_json = json.dumps(body, separators=(',', ':'))
    body_hash = hashlib.sha256(body_json.encode()).hexdigest()

    canonical = f"{method.upper()}\n{path}\n{timestamp}\n{request_id}\n{body_hash}"
    signature = hmac.new(SECRET_KEY.encode(), canonical.encode(), hashlib.sha256).hexdigest()

    return {
        "X-Request-Id": request_id,
        "X-Idempotency-Key": idempotency_key,
        "X-Timestamp": timestamp,
        "X-Signature": signature,
        "Content-Type": "application/json"
    }

def test_valid_event_accepted():
    payload = {"source": "skyfarm", "tenant_id": "sf_01", "type": "TEST", "data": {"val": 1}}
    headers = generate_headers("POST", "/integration/v1/events/production", payload)
    response = client.post("/integration/v1/events/production", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "accepted"

def test_malformed_event_rejected():
    payload = {"bad_field": "data"}
    headers = generate_headers("POST", "/integration/v1/events/production", payload)
    response = client.post("/integration/v1/events/production", json=payload, headers=headers)
    assert response.status_code == 422

def test_invalid_signature_rejected():
    payload = {"source": "skyfarm", "tenant_id": "sf_01", "type": "TEST", "data": {"val": 1}}
    headers = generate_headers("POST", "/integration/v1/events/production", payload)
    headers["X-Signature"] = "wrong"
    response = client.post("/integration/v1/events/production", json=payload, headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "INVALID_SIGNATURE"

def test_idempotent_event_handled():
    payload = {"source": "skyfarm", "tenant_id": "sf_01", "type": "IDEM", "data": {"val": 1}}
    idem_key = str(uuid.uuid4())
    headers = generate_headers("POST", "/integration/v1/events/production", payload, idempotency_key=idem_key)

    # First call
    resp1 = client.post("/integration/v1/events/production", json=payload, headers=headers)
    assert resp1.status_code == 200
    id1 = resp1.json()["event_id"]

    # Second call with same idempotency key
    # Signature will be different because of new Request-Id, but Idempotency-Key is same
    headers2 = generate_headers("POST", "/integration/v1/events/production", payload, idempotency_key=idem_key)
    resp2 = client.post("/integration/v1/events/production", json=payload, headers=headers2)
    assert resp2.status_code == 200
    assert resp2.json()["event_id"] == id1

def test_policy_rejection_works():
    payload = {"source": "skyfarm", "tenant_id": "sf_01", "type": "TEST", "data": {"test_deny": True}}
    headers = generate_headers("POST", "/integration/v1/events/production", payload)
    response = client.post("/integration/v1/events/production", json=payload, headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "POLICY_REJECTION"

def test_replay_protection_works():
    payload = {"source": "skyfarm", "tenant_id": "sf_01", "type": "REPLAY", "data": {"val": 1}}
    req_id = str(uuid.uuid4())
    headers = generate_headers("POST", "/integration/v1/events/production", payload, request_id=req_id)

    # First call
    client.post("/integration/v1/events/production", json=payload, headers=headers)

    # Second call with same request_id
    headers2 = generate_headers("POST", "/integration/v1/events/production", payload, request_id=req_id)
    response = client.post("/integration/v1/events/production", json=payload, headers=headers2)
    assert response.status_code == 401
    assert response.json()["detail"] == "REPLAYED_REQUEST_ID"

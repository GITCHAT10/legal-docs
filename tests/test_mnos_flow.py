import pytest
import requests
import hashlib
import hmac
import time
import json
import multiprocessing
import uvicorn
import os
import sys

# Ensure local imports work
sys.path.append(os.getcwd())

from services.core.mnos_api.main import app as api_app
from services.core.eleone.main import app as eleone_app
from services.core.shadow.main import app as shadow_app
from services.core.mnos_router.main import app as router_app

SECRET = "mnos-prod-secret"

def sign_request(method, path, timestamp, idempotency_key, body):
    body_hash = hashlib.sha256(body.encode()).hexdigest()
    canonical = f"{method}|{path}|{timestamp}|{idempotency_key}|{body_hash}"
    return hmac.new(SECRET.encode(), canonical.encode(), hashlib.sha256).hexdigest()

def run_svc(app, port, env=None):
    if env:
        os.environ.update(env)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")

@pytest.fixture(scope="module")
def mnos_cluster():
    env = {
        "ROUTER_URL": "http://127.0.0.1:8003",
        "SHADOW_URL": "http://127.0.0.1:8002",
        "MNOS_GATEWAY_SECRET": SECRET
    }

    processes = [
        multiprocessing.Process(target=run_svc, args=(eleone_app, 8001)),
        multiprocessing.Process(target=run_svc, args=(shadow_app, 8002)),
        multiprocessing.Process(target=run_svc, args=(router_app, 8003)),
        multiprocessing.Process(target=run_svc, args=(api_app, 8000, env)),
    ]
    for p in processes:
        p.start()

    # Wait for start
    for _ in range(15):
        try:
            if requests.get("http://127.0.0.1:8000/health", timeout=1).status_code == 200:
                break
        except:
            time.sleep(1)

    yield
    for p in processes:
        p.terminate()

def test_mnos_api_health(mnos_cluster):
    resp = requests.get("http://127.0.0.1:8000/health")
    assert resp.status_code == 200

def test_mnos_decision_flow(mnos_cluster):
    method = "POST"
    path = "/mnos/v1/decision"
    ts = str(time.time())
    idem = "idem-mnos-001"
    body_dict = {"module": "xport", "action": "VERIFY", "payload": {"risk": 0.1}}
    body_json = json.dumps(body_dict)
    sig = sign_request(method, path, ts, idem, body_json)

    headers = {
        "X-Signature": sig,
        "X-Timestamp": ts,
        "X-Idempotency-Key": idem,
        "Content-Type": "application/json"
    }

    resp = requests.post(f"http://127.0.0.1:8000{path}", headers=headers, data=body_json)
    assert resp.status_code == 200
    assert resp.json()["decision"] == "APPROVE"

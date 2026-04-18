import pytest
import requests
import multiprocessing
import time
import uvicorn
import sys
import os

# Add root to sys.path to allow imports
sys.path.append(os.getcwd())

from services.eleone.main import app as eleone_app
from services.shadow.main import app as shadow_app
from services.svd.main import app as svd_app
from services.sal.main import app as sal_app
from services.bfi.main import app as bfi_app

def run_svc(app, port):
    uvicorn.run(app, host="127.0.0.1", port=port)

@pytest.fixture(scope="module", autouse=True)
def setup_services():
    processes = [
        multiprocessing.Process(target=run_svc, args=(eleone_app, 8001)),
        multiprocessing.Process(target=run_svc, args=(shadow_app, 8002)),
        multiprocessing.Process(target=run_svc, args=(svd_app, 8003)),
        multiprocessing.Process(target=run_svc, args=(sal_app, 8004)),
        multiprocessing.Process(target=run_svc, args=(bfi_app, 8005)),
    ]
    for p in processes:
        p.start()

    time.sleep(2)
    yield
    for p in processes:
        p.terminate()

def test_eleone_decision():
    resp = requests.post("http://127.0.0.1:8001/decide", json={
        "item": "Tuna", "quantity": 100, "price": 5000, "vendor_id": "V-01"
    })
    assert resp.status_code == 200
    assert resp.json()["approved"] is True

def test_shadow_ledger():
    data = {"tx_id": "TX-123", "amount": 5000}
    resp = requests.post("http://127.0.0.1:8002/entry", json=data)
    assert resp.status_code == 200
    assert "current_hash" in resp.json()

    verify_resp = requests.get("http://127.0.0.1:8002/verify")
    assert verify_resp.json()["status"] == "valid"

def test_svd_verification():
    resp = requests.post("http://127.0.0.1:8003/verify?item_type=Fish")
    assert resp.status_code == 200
    assert resp.json()["verified"] is True

def test_sal_logging():
    payload = {"user": "admin", "action": "login"}
    resp = requests.post("http://127.0.0.1:8004/log?service=WEB&action=AUTH", json=payload)
    assert resp.status_code == 200

    query_resp = requests.get("http://127.0.0.1:8004/query")
    assert len(query_resp.json()) > 0

def test_bfi_transfer():
    data = {"amount": 1000.0, "currency": "USD", "recipient_iban": "MV12345", "reference": "REF-001"}
    resp = requests.post("http://127.0.0.1:8005/transfer", json=data)
    assert resp.status_code == 200
    assert "xml_payload" in resp.json()

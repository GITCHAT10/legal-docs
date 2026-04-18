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
        multiprocessing.Process(target=run_svc, args=(eleone_app, 8011)),
        multiprocessing.Process(target=run_svc, args=(shadow_app, 8012)),
        multiprocessing.Process(target=run_svc, args=(svd_app, 8013)),
        multiprocessing.Process(target=run_svc, args=(sal_app, 8014)),
        multiprocessing.Process(target=run_svc, args=(bfi_app, 8015)),
    ]
    for p in processes:
        p.start()

    time.sleep(3)
    yield
    for p in processes:
        p.terminate()

@pytest.mark.integration
def test_eleone_health():
    resp = requests.get("http://127.0.0.1:8011/health")
    assert resp.status_code == 200

@pytest.mark.integration
def test_shadow_entry():
    data = {"tx_id": "TX-123"}
    resp = requests.post("http://127.0.0.1:8012/entry", json=data)
    assert resp.status_code == 200
    assert "current_hash" in resp.json()

@pytest.mark.integration
def test_svd_health():
    resp = requests.get("http://127.0.0.1:8013/health")
    assert resp.status_code == 200

@pytest.mark.integration
def test_sal_health():
    resp = requests.get("http://127.0.0.1:8014/health")
    assert resp.status_code == 200

@pytest.mark.integration
def test_bfi_health():
    resp = requests.get("http://127.0.0.1:8015/health")
    assert resp.status_code == 200

import pytest
import requests
import multiprocessing
import time
import uvicorn
import sys
import os

# Add root to sys.path to allow imports
sys.path.append(os.getcwd())

from services.gateway.main import app as gateway_app
from services.eleone.main import app as eleone_app

def run_svc(app, port, env=None):
    if env:
        os.environ.update(env)
    uvicorn.run(app, host="127.0.0.1", port=port)

@pytest.fixture(scope="module", autouse=True)
def setup_services():
    env = {"ELEONE_URL": "http://127.0.0.1:8011"}

    p1 = multiprocessing.Process(target=run_svc, args=(eleone_app, 8011))
    p2 = multiprocessing.Process(target=run_svc, args=(gateway_app, 8010, env))

    p1.start()
    p2.start()

    time.sleep(3)
    yield
    p1.terminate()
    p2.terminate()

def test_gateway_proxy_eleone():
    resp = requests.post("http://127.0.0.1:8010/api/v1/eleone/decide", json={
        "item": "Tuna", "quantity": 100, "price": 5000, "vendor_id": "V-01"
    })
    assert resp.status_code == 200
    assert resp.json()["approved"] is True

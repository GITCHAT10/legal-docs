import pytest
import requests
import time
import multiprocessing
import uvicorn
import os
import sys

# Ensure local imports work
sys.path.append(os.getcwd())

from core.eleone.api.main import app as eleone_app
from core.shadow.api.main import app as shadow_app
from interfaces.gateway.api.main import app as gateway_app

def run_svc(app, port):
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")

@pytest.fixture(scope="module")
def cluster():
    processes = [
        multiprocessing.Process(target=run_svc, args=(eleone_app, 8081)),
        multiprocessing.Process(target=run_svc, args=(shadow_app, 8082)),
        multiprocessing.Process(target=run_svc, args=(gateway_app, 8080)),
    ]
    for p in processes: p.start()

    # Wait
    for _ in range(15):
        try:
            if requests.get("http://127.0.0.1:8080/health").status_code == 200:
                break
        except:
            time.sleep(1)

    yield
    for p in processes: p.terminate()

def test_mnos_health(cluster):
    assert requests.get("http://127.0.0.1:8080/health").status_code == 200
    assert requests.get("http://127.0.0.1:8081/health").status_code == 200
    assert requests.get("http://127.0.0.1:8082/health").status_code == 200

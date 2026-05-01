import pytest
import os
import subprocess
import sys
from fastapi.testclient import TestClient

def test_nexgen_secret_regression():
    env = os.environ.copy()
    if "NEXGEN_SECRET" in env: del env["NEXGEN_SECRET"]
    result = subprocess.run([sys.executable, "main.py"], env=env, capture_output=True, text=True)
    assert "FAIL CLOSED: NEXGEN_SECRET" in result.stderr

def test_event_bus_regression():
    from mnos.modules.events.bus import DistributedEventBus
    bus = DistributedEventBus()
    with pytest.raises(PermissionError):
        bus.publish("ROGUE_EVENT", {})

def test_tourism_pricing_regression():
    from mnos.modules.tourism.engine import TourismEngine
    from unittest.mock import MagicMock
    core = MagicMock()
    tourism = TourismEngine(core)
    with pytest.raises(ValueError):
        tourism._internal_book({"package_id": "P1"})

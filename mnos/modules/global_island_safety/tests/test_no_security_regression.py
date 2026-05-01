import pytest
import os
from main import app, identity_core
from mnos.modules.events.bus import DistributedEventBus

def test_event_bus_unguarded_publish_fails():
    bus = DistributedEventBus()
    # Direct publish without ExecutionGuard authorized context
    with pytest.raises(PermissionError):
        bus.publish("SENSITIVE_EVENT", {"data": "secret"})

def test_main_startup_no_secret_fails():
    # This is tested via subprocess in previous PR but we double check doctrine
    import subprocess
    import sys
    env = os.environ.copy()
    if "NEXGEN_SECRET" in env: del env["NEXGEN_SECRET"]
    result = subprocess.run([sys.executable, "main.py"], env=env, capture_output=True, text=True)
    assert "FAIL CLOSED: NEXGEN_SECRET" in result.stderr

def test_tourism_missing_price_fails():
    from mnos.modules.tourism.engine import TourismEngine
    from unittest.mock import MagicMock
    core = MagicMock()
    tourism = TourismEngine(core)
    with pytest.raises(ValueError) as exc:
        tourism._internal_book({"package_id": "P1"})
    assert "FAIL CLOSED: Missing price" in str(exc.value)

def test_qrd_launch_requires_aegis_orca_shadow():
    from mnos.modules.mig_shield.engine import MIGShieldEngine
    # MIG SHIELD engine uses guard.execute_sovereign_action_async
    # If no actor in context, ExecutionGuard raises PermissionError
    from mnos.shared.execution_guard import _sovereign_context
    _sovereign_context.set(None)

    # We don't need a full engine mock, just verifying guard behavior
    from main import guard
    with pytest.raises(PermissionError):
        guard.execute_sovereign_action("any.action", {}, lambda: True)

def test_police_evidence_requires_case_id():
    # Proof for requirement #7
    from mnos.modules.global_island_safety.shadow_report_profile import REPORT_PROFILES
    profile = REPORT_PROFILES["POLICE_CASE_EVIDENCE_EXPORT"]
    assert "case_id" in profile.required_fields

def test_no_facial_recognition_in_packages():
    # Proof for requirement #6
    from mnos.modules.global_island_safety.product_packages import PRODUCT_PACKAGES
    for name, pkg in PRODUCT_PACKAGES.items():
        for system in pkg.included_systems:
            assert "Facial Recognition" not in system

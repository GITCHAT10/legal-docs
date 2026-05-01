import pytest
from mnos.modules.global_island_safety.emergency_workflows import EMERGENCY_WORKFLOWS

def test_emergency_workflows_load():
    required = ["DROWNING", "MEDICAL", "FIRE_SMOKE", "MISSING_GUEST", "JETTY_BOAT_INCIDENT"]
    for r in required:
        assert r in EMERGENCY_WORKFLOWS

def test_workflow_steps():
    for name, steps in EMERGENCY_WORKFLOWS.items():
        assert len(steps) >= 3

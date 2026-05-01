import pytest
from mnos.modules.global_island_safety.compliance_registry import get_compliance_for_country

def test_compliance_registry_load():
    mv = get_compliance_for_country("MV")
    assert mv["mndf_approval_required"] is True
    assert mv["max_altitude_m"] == 120

def test_default_compliance():
    other = get_compliance_for_country("UNKNOWN")
    assert other["basic_aviation_permit"] is True

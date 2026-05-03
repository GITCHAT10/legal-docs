import pytest
from mnos.core.events.namespace_mapping import validate_namespace

def test_core_flexible():
    assert validate_namespace("CORE", "ANY.EVENT.TYPE")
    assert validate_namespace("EDGE_NODE", "ANY.OTHER.TYPE")

def test_mapped_namespaces():
    assert validate_namespace("QRD_MIG_SHIELD", "QRD.LAUNCH.APPROVE")
    assert not validate_namespace("QRD_MIG_SHIELD", "OTHER.LAUNCH.APPROVE")

    assert validate_namespace("ESG_TERRAFORM", "ESG.CLAIM.VERIFY")
    assert not validate_namespace("ESG_TERRAFORM", "NOT_ESG.CLAIM.VERIFY")

    assert validate_namespace("MARS_PEOPLE", "PEOPLE.DUTY.ASSIGN")
    assert validate_namespace("MARS_PEOPLE_HR", "PEOPLE.DUTY.ASSIGN")
    assert not validate_namespace("MARS_PEOPLE", "MARS.DUTY.ASSIGN")

def test_unmapped_allows():
    # Requirement 6 says CORE and EDGE_NODE must remain flexible.
    # Requirement 5 lists specific guards.
    # If a system is not in the guard list, we currently allow it in the implementation.
    assert validate_namespace("MAC_EOS", "MAC_EOS.BOOKING.CREATE")

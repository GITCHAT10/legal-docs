import pytest
from mnos.core.isolation.tenant_guard import TenantGuard

def test_tenant_isolation_match():
    event = {"context": {"tenant": {"brand": "SALA", "tin": "MV123"}}}
    target = {"brand": "SALA", "tin": "MV123"}
    assert TenantGuard.validate_isolation(event, target)

def test_tenant_isolation_mismatch_tin():
    event = {"context": {"tenant": {"brand": "SALA", "tin": "MV123"}}}
    target = {"brand": "SALA", "tin": "MV456"}
    assert not TenantGuard.validate_isolation(event, target)

def test_cross_tin_settlement_blocked():
    assert not TenantGuard.check_cross_tin_settlement("TIN1", "TIN2")
    assert TenantGuard.check_cross_tin_settlement("TIN1", "TIN1")

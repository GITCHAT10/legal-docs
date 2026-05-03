import pytest
from mnos.pilots.sala.run_pilot_flow import run_pilot
from mnos.core.fce.models import SettlementStatus
from mnos.core.fce.tax_engine_mv import calculate_maldives_tax

def test_sala_pilot_integration():
    results = run_pilot()

    assert results["settlement_status"] == SettlementStatus.APPROVED

    # Verify tax calculation matches expectation for 1000 base
    tax = calculate_maldives_tax(1000.00)
    assert tax.customer_total == 1287.00

    # Verify events
    assert results["booking_event"]["event_type"] == "MAC_EOS.BOOKING.CREATE"
    assert results["sale_event"]["event_type"] == "UPOS.SALE.COMPLETE"

def test_sala_pilot_failure_missing_tin():
    from mnos.pilots.sala.sample_events.events import get_upos_sale_complete
    from mnos.core.fce.settlement_guard import SettlementGuard

    tenant = {"brand": "SALA", "jurisdiction": "MV"} # Missing TIN
    event = get_upos_sale_complete(tenant)
    guard = SettlementGuard(None)
    status, msg = guard.validate_settlement(event)
    assert status == SettlementStatus.BLOCKED_TENANT_SCOPE

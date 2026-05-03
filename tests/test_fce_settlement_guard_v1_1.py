import pytest
import uuid
from datetime import datetime, UTC
from mnos.core.fce.settlement_guard import SettlementGuard
from mnos.core.fce.models import SettlementStatus

@pytest.fixture
def guard():
    return SettlementGuard(shadow_ledger=None)

def create_valid_settlement_event():
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "UPOS.SALE.COMPLETE",
        "timestamp": datetime.now(UTC).isoformat(),
        "source": { "system": "UPOS" },
        "actor": { "id": "user1", "role": "MERCHANT" },
        "context": {
            "tenant": { "brand": "SALA", "tin": "MV123", "jurisdiction": "MV" }
        },
        "payload": { "transaction_id": "TXN-1", "total_amount": 1287.00, "currency": "USD" },
        "proof": {
            "shadow_chain_ref": "SHADOW-1",
            "orca_validation": { "validated": True }
        },
        "metadata": { "schema_version": "1.1" }
    }

def test_settlement_approved(guard):
    event = create_valid_settlement_event()
    status, msg = guard.validate_settlement(event)
    assert status == SettlementStatus.APPROVED

def test_settlement_duplicate(guard):
    event = create_valid_settlement_event()
    status, msg = guard.validate_settlement(event)
    assert status == SettlementStatus.APPROVED

    status, msg = guard.validate_settlement(event)
    assert status == SettlementStatus.BLOCKED_DUPLICATE_IDEMPOTENCY

def test_settlement_missing_tenant(guard):
    event = create_valid_settlement_event()
    del event["context"]["tenant"]
    status, msg = guard.validate_settlement(event)
    assert status == SettlementStatus.BLOCKED_TENANT_SCOPE

def test_settlement_missing_shadow_proof(guard):
    event = create_valid_settlement_event()
    # requirement says .SETTLEMENT.COMPLETE or .SETTLED
    event["event_type"] = "FCE.SETTLEMENT.COMPLETE"
    del event["proof"]["shadow_chain_ref"]
    status, msg = guard.validate_settlement(event)
    assert status == SettlementStatus.BLOCKED_MISSING_SHADOW_PROOF

def test_settlement_unsupported_currency(guard):
    event = create_valid_settlement_event()
    event["payload"]["currency"] = "EUR"
    status, msg = guard.validate_settlement(event)
    assert status == SettlementStatus.BLOCKED_UNSUPPORTED_CURRENCY

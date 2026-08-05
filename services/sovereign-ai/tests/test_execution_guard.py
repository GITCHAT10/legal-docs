import json
from uuid import uuid4

import pytest

from app.finance.execution_guard import SecurityError, SovereignExecutionGuard


def payload(**overrides):
    body = {
        "proposal_type": "JOURNAL_ENTRY",
        "legal_entity_id": str(uuid4()),
        "origin_agent_id": str(uuid4()),
        "currency": "USD",
        "effective_date": "2026-08-05",
        "idempotency_key": "guard-test-0001",
        "lines": [
            {"account_code": "1100", "debit": "1000.00", "credit": "0.00"},
            {"account_code": "4100", "debit": "0.00", "credit": "1000.00"},
        ],
    }
    body.update(overrides)
    return json.dumps(body)


def test_balanced_proposal_is_quarantined_not_posted():
    decision = SovereignExecutionGuard().evaluate_proposal(payload())
    assert decision["decision"] == "AWAITING_APPROVAL"
    assert decision["ledger_posted"] is False
    assert decision["risk_class"] == "CLASS_3"
    assert decision["required_approvals"] == 2


def test_unbalanced_proposal_fails_closed():
    with pytest.raises(SecurityError, match="Ledger unbalanced"):
        SovereignExecutionGuard().evaluate_proposal(payload(lines=[
            {"account_code": "1100", "debit": "100.00", "credit": "0.00"},
            {"account_code": "4100", "debit": "0.00", "credit": "99.99"},
        ]))


def test_unknown_account_fails_closed():
    with pytest.raises(SecurityError, match="Invalid account"):
        SovereignExecutionGuard().evaluate_proposal(payload(lines=[
            {"account_code": "9999", "debit": "1.00", "credit": "0.00"},
            {"account_code": "4100", "debit": "0.00", "credit": "1.00"},
        ]))


def test_sub_cent_precision_rejected():
    with pytest.raises(ValueError, match="Invalid precision"):
        SovereignExecutionGuard().evaluate_proposal(payload(lines=[
            {"account_code": "1100", "debit": "1.001", "credit": "0.00"},
            {"account_code": "4100", "debit": "0.00", "credit": "1.001"},
        ]))


def test_zero_zero_line_rejected():
    with pytest.raises(SecurityError, match="exclusivity"):
        SovereignExecutionGuard().evaluate_proposal(payload(lines=[
            {"account_code": "1100", "debit": "0.00", "credit": "0.00"},
        ]))


def test_hash_is_deterministic_for_same_canonical_payload():
    raw = payload()
    guard = SovereignExecutionGuard()
    assert guard.evaluate_proposal(raw)["proposal_hash"] == guard.evaluate_proposal(raw)["proposal_hash"]

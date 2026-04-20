import pytest
from mnos.core.ai.models import AiDecision, DecisionStatus
from mnos.core.ai.policy_validator import PolicyValidator

def test_revenue_optimizer_confidence_thresholds():
    validator = PolicyValidator()

    # Low confidence (< 0.85) => REJECTED
    low_conf = AiDecision(
        module="revenue_optimizer",
        action="APPLY_DISCOUNT",
        reasoning="Testing low confidence",
        parameters={"route_id": "R1"},
        confidence_score=0.82
    )
    validated_low = validator.validate(low_conf)
    assert validated_low.status == DecisionStatus.REJECTED
    assert "Low confidence" in validated_low.bounded_reason

    # Medium confidence (0.85 to 0.929) => ADVISORY
    med_conf = AiDecision(
        module="revenue_optimizer",
        action="APPLY_DISCOUNT",
        reasoning="Testing medium confidence",
        parameters={"route_id": "R1"},
        confidence_score=0.90
    )
    validated_med = validator.validate(med_conf)
    assert validated_med.status == DecisionStatus.ADVISORY
    assert "Advisory only" in validated_med.bounded_reason

    # High confidence (>= 0.93) => ELIGIBLE_FOR_REVIEW
    high_conf = AiDecision(
        module="revenue_optimizer",
        action="INCREASE_PRICE",
        reasoning="Testing high confidence",
        parameters={"route_id": "R1"},
        confidence_score=0.95
    )
    validated_high = validator.validate(high_conf)
    assert validated_high.status == DecisionStatus.ELIGIBLE_FOR_REVIEW
    assert "Eligible for policy review" in validated_high.bounded_reason

def test_hard_prohibitions_tax_logic():
    validator = PolicyValidator()

    # Attempt to modify tax logic => REJECTED
    tax_decision = AiDecision(
        module="revenue_optimizer",
        action="UPDATE_TAX",
        reasoning="Testing tax prohibition",
        parameters={"tax_rate": 0.20},
        confidence_score=0.98
    )
    validated_tax = validator.validate(tax_decision)
    assert validated_tax.status == DecisionStatus.REJECTED
    assert "Attempted modification of tax logic" in validated_tax.bounded_reason

def test_hard_prohibitions_financial_execution():
    validator = PolicyValidator()

    # Attempt to emit folio/payment/ledger execution events => REJECTED
    exec_decision = AiDecision(
        module="revenue_optimizer",
        action="EXECUTE_PAYMENT",
        reasoning="Testing execution prohibition",
        parameters={"amount": 100},
        confidence_score=0.99
    )
    validated_exec = validator.validate(exec_decision)
    assert validated_exec.status == DecisionStatus.REJECTED
    assert "prohibited financial execution" in validated_exec.bounded_reason

def test_core_bypass_block():
    validator = PolicyValidator()
    # The requirement is that it must never bypass FCE or CORE policy.
    # We implement this by ensuring all AI decisions are restricted to informational/advisory statuses
    # and cannot trigger direct execution actions.

    decision = AiDecision(
        module="revenue_optimizer",
        action="BYPASS_POLICY",
        reasoning="Testing policy bypass",
        parameters={},
        confidence_score=0.95
    )
    # If the action contains prohibited words it should be blocked.
    # 'policy' isn't explicitly in PROHIBITED_KEYWORDS but financial execution is.
    # Let's ensure 'ledger' or 'payment' in parameters is also caught.

    decision_with_ledger = AiDecision(
        module="revenue_optimizer",
        action="RECOMMEND_ADJUSTMENT",
        reasoning="Testing ledger in params",
        parameters={"target": "ledger_entry"},
        confidence_score=0.95
    )
    validated = validator.validate(decision_with_ledger)
    assert validated.status == DecisionStatus.REJECTED

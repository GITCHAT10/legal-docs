import os

from mnos.modules.marketing.anthropic_router import AnthropicModelPolicy, Workload


def test_standard_routes_to_sonnet():
    decision = AnthropicModelPolicy().choose(Workload.STANDARD)
    assert decision.model_id == "claude-sonnet-5"
    assert decision.require_human_approval is False


def test_complex_requires_human_approval():
    decision = AnthropicModelPolicy().choose(Workload.COMPLEX)
    assert decision.model_id == "claude-opus-4-8"
    assert decision.require_human_approval is True


def test_frontier_routes_to_fable_with_opus_fallback():
    decision = AnthropicModelPolicy().choose(Workload.FRONTIER)
    assert decision.model_id == "claude-fable-5"
    assert decision.fallback_model_id == "claude-opus-4-8"


def test_security_review_fails_closed_to_fable(monkeypatch):
    monkeypatch.delenv("MIG_ENABLE_RESTRICTED_MYTHOS", raising=False)
    decision = AnthropicModelPolicy().choose(Workload.SECURITY_REVIEW)
    assert decision.model_id == "claude-fable-5"
    assert decision.require_human_approval is True


def test_mythos_requires_explicit_restricted_access(monkeypatch):
    monkeypatch.setenv("MIG_ENABLE_RESTRICTED_MYTHOS", "true")
    decision = AnthropicModelPolicy().choose(Workload.SECURITY_REVIEW)
    assert decision.model_id == "claude-mythos-5"
    assert decision.require_human_approval is True


def test_personal_data_forces_approval():
    decision = AnthropicModelPolicy().choose(
        Workload.STANDARD, contains_personal_data=True
    )
    assert decision.require_human_approval is True
